from .barrier import region_ids
"""Repeatable post-campaign challenges; the server never advances its edition."""
from datetime import timedelta
from uuid import UUID
from django.db.models import Sum,Max
from django.utils import timezone
from .models import FrontierProgress,FrontierRecord
from .game_logic import player_action,simulate_combat,check_level_up
from .world_clock import polish_day

MAX_DEPTH=100
COOLDOWN=timedelta(minutes=5)


def frontier_unlocked(profile):
    """Sandbox progression depends on earned level and camp, not the story ending."""
    return profile.level >= 30 and profile.camp != 'NONE'


def season_key(now=None):
    return polish_day(now).strftime('%Y-%m')


def enemy(depth):
    return {'nazwa':f'Strażnik wyłomu — warta {depth}','life':600+60*depth,'strength':55+3*depth,'weapon_prot':25+2*depth,'magic_prot':10+depth,'fire_prot':10+depth}


def board(world):
    return FrontierRecord.objects.filter(profile__world_id__in=region_ids(world),profile__user__is_active=True,profile__user__is_staff=False,season=season_key(),won=True).values('profile_id','profile__user__username','profile__is_bot','profile__camp').annotate(points=Sum('points'),depth=Max('depth')).order_by('-points','-depth','profile_id')[:30]


@player_action
def patrol(profile,depth,key):
    try:key=UUID(str(key))
    except (ValueError,TypeError,AttributeError):return False
    prior=FrontierRecord.objects.filter(profile=profile,request_key=key).first()
    if prior:return prior if prior.depth==depth else False
    if type(depth)is not int or not 1<=depth<=MAX_DEPTH or not frontier_unlocked(profile):return False
    if profile.is_busy or profile.current_energy<20 or profile.current_health<10:return False
    progress,_=FrontierProgress.objects.select_for_update().get_or_create(profile=profile)
    now=timezone.now()
    if depth>progress.unlocked or (progress.last_attempt_at and now<progress.last_attempt_at+COOLDOWN):return False
    from .magic import combat_plan,apply_combat_magic
    from .equipment import consume_ammo
    plan=combat_plan(profile)
    if profile.prepared_magic_id and (not plan or profile.current_mana<plan.cost):return False
    if not plan and not consume_ammo(profile):return False
    result=simulate_combat(profile,'frontier',monster=enemy(depth),magic_plan=plan)
    apply_combat_magic(profile,plan,result)
    profile.current_health=result.remaining_health;profile.health_updated_at=now;profile.current_energy-=20
    loot=[];ore=experience=0
    first=not FrontierRecord.objects.filter(profile=profile,depth=depth,won=True).exists()
    if result.won:
        from .world_events import reward_snapshot
        ore,experience,_,_=reward_snapshot(50+10*depth,400+80*depth)
        profile.ore_balance+=ore;profile.experience+=experience;check_level_up(profile)
        from .gear_loot import award_gear
        loot=award_gear(profile,30,boss=True,guaranteed=first)
        progress.wins+=1;progress.unlocked=min(MAX_DEPTH, max(progress.unlocked,depth+1))
    profile.save();progress.last_attempt_at=now;progress.save()
    points=depth*10 if result.won else 0
    row=FrontierRecord.objects.create(profile=profile,request_key=key,depth=depth,season=season_key(now),won=result.won,points=points,snapshot={'version':1,'enemy':enemy(depth),'ore':ore,'experience':experience,'loot':loot,'log':result.log,'health':profile.current_health,'energy_cost':20,'magic':plan.spell.key if plan else None,'casts':result.spell_casts})
    if result.won:
        from .camp_progression import record_camp_event
        record_camp_event(profile,'hunt:frontier')
    return row
