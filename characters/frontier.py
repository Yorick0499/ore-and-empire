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


def presentation(profile):
    from .barrier import joined,region
    if joined(profile.world_id):
        complete=profile.story_runs.filter(status='claimed',quest__key='nk-undead').exists()
        return {'title':'Warty wspólnych szlaków','label':'Służba po upadku Bariery',
                'art':'nk_region_irdorath' if complete else 'nk_region_valley',
                'description':'Wyprawa do Irdorath dobiegła końca, ale wspólny świat żyje dalej. Wracaj na warty, ulepszaj sprzęt i zdobywaj wynik miesiąca.' if complete else 'Kolonia i Khorinis tworzą wspólny świat. Ochraniaj szlaki i rozwijaj ekwipunek pomiędzy przydziałami.'}
    if region(profile).universe=='GOTHIC_II':
        return {'title':'Warty Khorinis','label':'Służba na wyspie','art':'k2_harbor','description':'Bariera nadal stoi. Utrzymuj szlaki wyspy, zdobywaj lepszy sprzęt i wspieraj swoją wspólnotę.'}
    return {'title':'Warty za Przełęczą','label':'Służba w Kolonii','art':'old_camp','description':'Bariera nadal stoi. Obóz potrzebuje wartowników; trenuj, zdobywaj oręż i ulepszaj wyposażenie. Osobista kampania nie kończy życia świata.'}


def season_key(now=None):
    return polish_day(now).strftime('%Y-%m')


def enemy(depth,track="legacy"):
    if track!="legacy":
        from .regional_endgame import enemy as regional_enemy
        return regional_enemy(depth,track)
    return {'nazwa':f'Strażnik wyłomu — warta {depth}','life':600+60*depth,'strength':55+3*depth,'weapon_prot':25+2*depth,'magic_prot':10+depth,'fire_prot':10+depth}


def board(world,track=None):
    rows=FrontierRecord.objects.all()
    if track is not None:rows=rows.filter(track=track)
    return rows.filter(profile__world_id__in=region_ids(world),profile__user__is_active=True,profile__user__is_staff=False,season=season_key(),won=True).values('profile_id','profile__user__username','profile__is_bot','profile__camp').annotate(points=Sum('points'),depth=Max('depth')).order_by('-points','-depth','profile_id')[:30]


@player_action
def patrol(profile,depth,key,track="legacy"):
    try:key=UUID(str(key))
    except (ValueError,TypeError,AttributeError):return False
    prior=FrontierRecord.objects.filter(profile=profile,request_key=key).first()
    if prior:return prior if prior.depth==depth and prior.track==track else False
    from .regional_endgame import TRACKS,accessible,fee,rewarded_today,DAILY_REWARDS
    if type(track)is not str:return False
    if track!="legacy" and (track not in TRACKS or not accessible(profile,track)):return False
    if type(depth)is not int or not 1<=depth<=MAX_DEPTH or not frontier_unlocked(profile):return False
    if profile.is_busy or profile.current_energy<20 or profile.current_health<10:return False
    progress,_=FrontierProgress.objects.select_for_update().get_or_create(profile=profile)
    now=timezone.now()
    route_progress=progress
    if track!="legacy":
        from .models import RegionalFrontierProgress
        route_progress,_=RegionalFrontierProgress.objects.select_for_update().get_or_create(profile=profile,track=track)
    charge=0 if track=="legacy" else fee(depth)
    if profile.ore_balance<charge:return False
    if depth>route_progress.unlocked or (progress.last_attempt_at and now<progress.last_attempt_at+COOLDOWN):return False
    from .magic import combat_plan,apply_combat_magic
    from .equipment import consume_ammo
    plan=combat_plan(profile)
    if profile.prepared_magic_id and (not plan or profile.current_mana<plan.cost):return False
    if not plan and not consume_ammo(profile):return False
    result=simulate_combat(profile,'frontier',monster=enemy(depth,track),magic_plan=plan)
    apply_combat_magic(profile,plan,result)
    profile.current_health=result.remaining_health;profile.health_updated_at=now;profile.current_energy-=20
    loot=[];ore=experience=0
    rewarded=track=="legacy" or rewarded_today(profile,now)<DAILY_REWARDS
    prior_wins=FrontierRecord.objects.filter(profile=profile,track=track,depth=depth,won=True)
    if track!="legacy":prior_wins=prior_wins.filter(snapshot__rewarded=True)
    first=not prior_wins.exists()
    profile.ore_balance-=charge
    if result.won:
        from .world_events import reward_snapshot
        if rewarded:
            ore,experience,_,_=reward_snapshot(50+10*depth if track=="legacy" else 80+5*min(depth,40),400+80*depth if track=="legacy" else 800+50*min(depth,40))
        profile.ore_balance+=ore;profile.experience+=experience;check_level_up(profile)
        from .gear_loot import award_gear
        if rewarded:loot=award_gear(profile,30,boss=True,guaranteed=first,source_game='GOTHIC_II' if track!='legacy' else None)
        route_progress.wins+=1;route_progress.unlocked=min(MAX_DEPTH,max(route_progress.unlocked,depth+1))
        route_progress.save()
    profile.save();progress.last_attempt_at=now;progress.save()
    points=depth*10 if result.won else 0
    row=FrontierRecord.objects.create(profile=profile,request_key=key,track=track,depth=depth,created_at=now,season=season_key(now),won=result.won,points=points,snapshot={'version':1 if track=='legacy' else 2,'track':track,'rewarded':bool(result.won and rewarded),'entry_fee':charge,'enemy':enemy(depth,track),'ore':ore,'experience':experience,'loot':loot,'log':result.log,'health':profile.current_health,'energy_cost':20,'magic':plan.spell.key if plan else None,'casts':result.spell_casts})
    if result.won:
        from .camp_progression import record_camp_event
        record_camp_event(profile,'hunt:frontier')
    return row
