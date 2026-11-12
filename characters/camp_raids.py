from .barrier import guild_for,raid_guild_ids
from .world_clock import POLISH_TIME
"""One shared opponent per camp and Polish calendar day, paid asynchronous three-round sorties."""
from datetime import datetime,time,timezone as utc,timedelta
from uuid import UUID
import random
from django.db.models import Sum,Q
from django.utils import timezone
from .models import CampGuild,CampRaid,CampRaidStrike,CampRaidReward
from .game_logic import player_action,CombatResult,check_level_up
from .camp_guilds import CAMPS,credit_guild

ENCOUNTERS={'OLD_CAMP':('Matka pełzaczy z bocznego szybu','crawler_queen'),'NEW_CAMP':('Orkowy zwiadowca przy zaporze','orc_warrior'),'SWAMP_CAMP':('Prastary wąż z rozlewiska','swampshark')}

ENCOUNTERS.update({'CITY_WATCH':('Banda z leśnego traktu','k2_goblin'),'FIRE_ORDER':('Warg spod klasztoru','k2_warg'),'ONAR_MERCS':('Bestia pustosząca pola','k2_field_raider')})

ENCOUNTERS.update({'BANDITS':ENCOUNTERS['OLD_CAMP'],'WATER_CIRCLE':ENCOUNTERS['NEW_CAMP'],'MERCENARIES':ENCOUNTERS['ONAR_MERCS']})


def phase(raid):
    return 1 if raid.health*100>raid.maximum_health*60 else 2 if raid.health*100>raid.maximum_health*25 else 3


@player_action
def rally_camp_raid(profile,cycle="daily"):
    if cycle not in {"daily","weekly"}:return False
    from .regional_endgame import unlocked,week_start,weekly_track
    if cycle=="weekly" and not unlocked(profile):return False
    from .camp_privileges import privileges
    if not privileges(profile)["can_rally"]:return False
    if profile.camp not in CAMPS:return False
    guild=guild_for(profile,lock=True)
    name,art=ENCOUNTERS[guild.camp];health=500+guild.level*100
    day=timezone.now().astimezone(POLISH_TIME).date()
    if cycle=='weekly':
        day=week_start();track=weekly_track(day);name='Tygodniowy cel: '+track.name;art=track.species[-1];health=10000+guild.level*1000
    raid,_=CampRaid.objects.get_or_create(guild=guild,day=day,cycle=cycle,defaults={'name':name,'art_key':art,'health':health,'maximum_health':health,'attack':100 if cycle=='weekly' else 10+guild.level*2,'protection':60 if cycle=='weekly' else 4+guild.level*2,'minimum_level':45 if cycle=='weekly' else 3})
    return raid


def exchange(profile,raid,plan):
    from .equipment import combat_values
    damage,skill,kind=combat_values(profile);health=profile.current_health;mana=profile.current_mana;casts=0;total=0;log=[]
    for turn in range(3):
        before=phase(raid)
        casting=bool(plan and mana>=plan.cost and (not plan.scroll or casts<plan.quantity))
        if casting:
            mana-=plan.cost;casts+=1;power=plan.spell.damage;attack_kind=plan.spell.damage_type
            log.append(f'{plan.spell.name}: wydano {plan.cost} many.')
        else:
            power=profile.strength+profile.equipment_stats['strength_bonus'] if plan else damage*(2 if random.randint(1,100)<=skill else 1)
            attack_kind='weapon' if plan else kind
        armor=raid.protection//2 if before==3 else raid.protection
        # This encounter has physical armor and a small ward, not an imported G1 stat.
        actual=min(raid.health,max(1,power-(armor if attack_kind in {'weapon','arrow'} else armor//2)))
        raid.health-=actual;total+=actual
        log.append(f'Etap {before}: zadajesz {actual} obrażeń; przeciwnik ma {raid.health}/{raid.maximum_health} zdrowia.')
        if raid.health<=0:log.append('Wspólnymi siłami obóz pokonał zagrożenie.');break
        after=phase(raid)
        if after!=before:log.append('Przeciwnik wpada w szał!' if after==2 else 'Odsłania pancerz i przygotowuje ostatni zryw!')
        incoming=max(1,raid.attack+(0 if after==1 else 5 if after==2 else 10)-profile.effective_protection('weapon'))
        if casting and plan.spell.stagger_every and casts%plan.spell.stagger_every==0:incoming=0;log.append('Zaklęcie przerywa atak przeciwnika.')
        elif casting and plan.spell.mitigation:incoming=max(1,incoming*(100-plan.spell.mitigation)//100)
        health-=incoming;log.append(f'Kontratak: tracisz {incoming} zdrowia.')
        if health<=0:health=1;log.append('Wycofujesz się ranny; twój rzeczywisty wkład pozostaje dla obozu.');break
    return CombatResult(raid.health==0,log,health,mana,casts),total


@player_action
def strike_camp_raid(profile,raid_id,request_key):
    try:key=UUID(str(request_key))
    except (ValueError,TypeError,AttributeError):return False
    prior=CampRaidStrike.objects.filter(profile=profile,request_key=key).first()
    if prior:return prior if prior.raid_id==raid_id and (prior.raid.guild_id in raid_guild_ids(profile) or prior.damage>0) else False
    if profile.camp not in CAMPS:return False
    guild=guild_for(profile,lock=True)
    from .regional_endgame import week_start,unlocked
    active=Q(cycle='daily',day=timezone.now().astimezone(POLISH_TIME).date())|Q(cycle='weekly',day=week_start())
    raid=CampRaid.objects.select_for_update().filter(active,pk=raid_id,guild_id__in=raid_guild_ids(profile)).first()
    if raid and raid.cycle=='weekly' and (raid.rule_version!=1 or not unlocked(profile)):return False
    if not raid or raid.completed_at or profile.level<raid.minimum_level or profile.is_busy or profile.current_energy<20 or profile.current_health<10:return False
    last=CampRaidStrike.objects.filter(raid=raid,profile=profile).first()
    if last and timezone.now()<last.created_at+timedelta(seconds=60):return False
    from .magic import combat_plan,apply_combat_magic
    from .equipment import consume_ammo
    plan=combat_plan(profile)
    if profile.prepared_magic_id and (not plan or profile.current_mana<plan.cost):return False
    if not plan and not consume_ammo(profile):return False
    before_health=profile.current_health;before_mana=profile.current_mana
    result,damage=exchange(profile,raid,plan)
    apply_combat_magic(profile,plan,result)
    profile.current_health=result.remaining_health;profile.health_updated_at=timezone.now();profile.current_energy-=20;profile.save()
    if raid.health==0:
        raid.completed_at=timezone.now();credit_guild(guild,60,100)
    raid.save(update_fields=['health','completed_at'])
    return CampRaidStrike.objects.create(raid=raid,profile=profile,request_key=key,damage=damage,health_cost=before_health-profile.current_health,mana_cost=before_mana-profile.current_mana,casts=result.spell_casts,log=result.log)


@player_action
def claim_camp_raid(profile,raid_id):
    raid=CampRaid.objects.filter(pk=raid_id,completed_at__isnull=False,strikes__profile=profile,strikes__damage__gt=0).first()
    if not raid or not raid.strikes.filter(profile=profile,damage__gt=0).exists():return False
    if CampRaidReward.objects.filter(raid=raid,profile=profile).exists():return True
    values={'ore':100,'experience':1000,'premium':0} if raid.cycle=='weekly' else {}
    reward=CampRaidReward.objects.create(raid=raid,profile=profile,**values)
    if raid.cycle=='weekly':
        from .equipment import add_item
        from .models import ItemBluePrint
        add_item(profile,ItemBluePrint.objects.get(catalog_key='rune-dust'),5,origin='reward')
    profile.ore_balance+=reward.ore;profile.experience+=reward.experience
    from .economy import change_premium
    if reward.premium:
        change_premium(profile,reward.premium,'Wkład w wyprawę obozową',f'camp-raid:{raid.pk}:{profile.pk}')
    from .challenges import record_personal_event
    record_personal_event(profile,'raid')
    check_level_up(profile);profile.save();return True


def raid_card(profile,cycle='daily'):
    from .regional_endgame import week_start,weekly_track,unlocked
    allowed=cycle=='daily' or (cycle=='weekly' and unlocked(profile))
    day=week_start() if cycle=='weekly' else timezone.now().astimezone(POLISH_TIME).date()
    raid=CampRaid.objects.filter(guild_id__in=raid_guild_ids(profile),day=day,cycle=cycle).first() if allowed else None
    rewards=CampRaid.objects.filter(cycle=cycle,completed_at__isnull=False,strikes__profile=profile,strikes__damage__gt=0).exclude(campraidreward__profile=profile).distinct().order_by('-day')[:10]
    ends=datetime.combine(day+timedelta(days=7 if cycle=='weekly' else 1),time.min,tzinfo=POLISH_TIME)
    if not raid:return {'raid':None,'rewards':rewards,'ends_at':ends,'preview':weekly_track(day) if cycle=='weekly' else None}
    last=raid.strikes.filter(profile=profile).first()
    ready=not last or timezone.now()>=last.created_at+timedelta(seconds=60)
    contributions=list(raid.strikes.values('profile_id','profile__user__username','profile__name','profile__is_bot').annotate(damage=Sum('damage')).order_by('-damage')[:30])
    from .models import PlayerProfile
    names={p.pk:p.display_name for p in PlayerProfile.objects.filter(pk__in=[row['profile_id'] for row in contributions]).select_related('user')}
    for row in contributions:row['name']=names[row['profile_id']]
    return {'raid':raid,'ends_at':ends,'phase':phase(raid),'can_attack':allowed and not raid.completed_at and ready and profile.level>=raid.minimum_level and profile.current_energy>=20 and profile.current_health>=10 and not profile.is_busy,
        'rewards':rewards,'contributions':contributions,'logs':raid.strikes.select_related('profile__user')[:10]}
