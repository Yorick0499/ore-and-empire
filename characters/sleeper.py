"""Persistent camp race; the final strike enqueues exactly one Barrier fall."""
from datetime import timedelta
from uuid import UUID
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from .models import World,CampGuild,SleeperRace,SleeperSiege,SleeperStrike,SleeperReward,BarrierEvent
from .game_logic import player_action
from .realms import G1

MINIMUM_ACCOUNTS=3


def eligible(profile):
    from .finale import finale_ready
    return profile.camp in G1 and profile.world.universe=='GOTHIC_I' and finale_ready(profile) and profile.camp_tier>=2


@player_action
def rally(profile):
    if not eligible(profile):return False
    from .camp_privileges import privileges
    if not privileges(profile)['can_rally']:return False
    guild=CampGuild.objects.select_for_update().get(world_id=profile.world_id,camp=profile.camp)
    if guild.level!=10:return False
    island=World.objects.filter(universe='GOTHIC_II',is_open=True,configured=True,status='active').first()
    if not island or not profile.world.is_current or not profile.world.configured or profile.world.union_key:return False
    race,_=SleeperRace.objects.get_or_create(colony_id=profile.world_id,defaults={'khorinis':island})
    race=SleeperRace.objects.select_for_update().get(pk=race.pk)
    if race.state!='racing' or race.paused:return False
    siege,created=SleeperSiege.objects.get_or_create(race=race,guild=guild)
    if created:BarrierEvent.objects.create(race=race,kind='rallied',details={'guild':guild.pk})
    return siege


@player_action
def strike(profile,siege_id,request_key):
    try:key=UUID(str(request_key))
    except (ValueError,TypeError,AttributeError):return False
    # Serialize all characters of one account, including different camps.
    User.objects.select_for_update().get(pk=profile.user_id)
    prior=SleeperStrike.objects.filter(account_id=profile.user_id,request_key=key).first()
    if prior:return prior if prior.profile_id==profile.pk and prior.siege_id==siege_id else False
    if not eligible(profile):return False
    race=SleeperRace.objects.select_for_update().filter(colony_id=profile.world_id).first()
    if not race or race.state!='racing' or race.paused:return False
    siege=SleeperSiege.objects.select_for_update().filter(pk=siege_id,race=race,guild__camp=profile.camp,guild__level=10).first()
    now=timezone.now()
    if not siege or siege.completed_at or profile.is_busy or profile.current_energy<25 or profile.current_health<50:return False
    last=SleeperStrike.objects.filter(account_id=profile.user_id).order_by('-created_at','-pk').first()
    if last and now<last.created_at+timedelta(seconds=60):return False
    accounts=set(siege.strikes.filter(damage__gt=0).values_list('account_id',flat=True));accounts.add(profile.user_id)
    floor=siege.maximum_health*max(0,MINIMUM_ACCOUNTS-len(accounts))//MINIMUM_ACCOUNTS
    if siege.health<=floor:return False  # Wait for another account, without spending resources.
    from .magic import combat_plan,apply_combat_magic
    from .equipment import consume_ammo
    from .camp_raids import exchange
    plan=combat_plan(profile)
    if profile.prepared_magic_id and (not plan or profile.current_mana<plan.cost):return False
    if not plan and not consume_ammo(profile):return False
    before=siege.health
    result,damage=exchange(profile,siege,plan)
    # Three distinct accounts must contribute before the seal can be broken.
    siege.health=max(siege.health,min(before,floor));damage=before-siege.health
    if floor and siege.health==floor:
        result.log[:]=[line for line in result.log if 'pokonał zagrożenie' not in line]
        result.log.append(f'Pieczęć wymaga wkładu trzech różnych kont. Po jej odpowiedzi pozostaje {siege.health}/{siege.maximum_health} HP.')
    apply_combat_magic(profile,plan,result)
    profile.current_health=result.remaining_health;profile.health_updated_at=now;profile.current_energy-=25;profile.save()
    hit=SleeperStrike.objects.create(siege=siege,profile=profile,account_id=profile.user_id,request_key=key,damage=damage,log=result.log)
    if siege.health==0:
        siege.completed_at=now;race.winner=siege.guild;race.won_at=now;race.state='pending';race.save(update_fields=['winner','won_at','state'])
        BarrierEvent.objects.create(race=race,kind='victory',details={'guild':siege.guild_id,'strike':hit.pk})
    siege.save(update_fields=['health','completed_at'])
    return hit


@player_action
def claim_reward(profile):
    User.objects.select_for_update().get(pk=profile.user_id)
    race=SleeperRace.objects.filter(colony_id=profile.world_id,winner__camp=profile.camp,state='joined').first()
    if not race or not SleeperStrike.objects.filter(siege__race=race,siege__guild=race.winner,account_id=profile.user_id,damage__gt=0).exists():return False
    if SleeperReward.objects.filter(race=race,account_id=profile.user_id).exists():return True
    SleeperReward.objects.create(race=race,account_id=profile.user_id,profile=profile)
    profile.ore_balance+=500;profile.experience+=1000
    from .economy import change_premium
    from .game_logic import check_level_up
    change_premium(profile,3,'Wkład w upadek Bariery',f'barrier:{race.pk}:{profile.user_id}')
    check_level_up(profile);profile.save();return True


def card(profile):
    race=SleeperRace.objects.filter(colony_id=profile.world_id).select_related('winner').first()
    siege=SleeperSiege.objects.filter(race=race,guild__camp=profile.camp).first() if race else None
    guild=CampGuild.objects.filter(world_id=profile.world_id,camp=profile.camp).first()
    last=SleeperStrike.objects.filter(account_id=profile.user_id).order_by('-created_at','-pk').first()
    ready=not last or timezone.now()>=last.created_at+timedelta(seconds=60)
    accounts=set(siege.strikes.filter(damage__gt=0).values_list('account_id',flat=True)) if siege else set()
    floor=siege.maximum_health*max(0,MINIMUM_ACCOUNTS-len(accounts|{profile.user_id}))//MINIMUM_ACCOUNTS if siege else 0
    seal_blocked=bool(siege and race.state=='racing' and floor and siege.health<=floor)
    return {'race':race,'siege':siege,'eligible':eligible(profile),'guild_ready':bool(guild and guild.level==10),'cooldown_ready':ready,
            'seal_blocked':seal_blocked,'can_strike':bool(siege and not seal_blocked and race.state=='racing' and not race.paused and eligible(profile) and ready and not profile.is_busy and profile.current_energy>=25 and profile.current_health>=50),
            'contributions':list(siege.strikes.filter(damage__gt=0).values('account_id').distinct()) if siege else [],'logs':siege.strikes.select_related('profile__user')[:10] if siege else []}
