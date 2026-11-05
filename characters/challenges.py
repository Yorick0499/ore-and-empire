from .world_clock import POLISH_TIME
"""Bounded personal goals; Polish calendar periods, immutable rewards, shared rules for bots."""
from datetime import timedelta,timezone as utc
from django.utils import timezone
from .models import PersonalChallenge,PlayerAchievement,CampReputation
from .game_logic import player_action,check_level_up

ACHIEVEMENTS={'miner':('Dziesięć zmian','mine',10),'hunter':('Strażnik szlaków','hunt',10),'raider':('Wspólne zwycięstwo','raid',1),'artisan':('Pięć dzieł rzemiosła','craft',5)}


def period_for(cadence,now=None):
    day=(now or timezone.now()).astimezone(POLISH_TIME).date()
    return day if cadence=='daily' else day-timedelta(days=day.weekday())


@player_action
def accept_challenge(profile,cadence):
    if cadence not in {'daily','weekly'}:return False
    period=period_for(cadence)
    if PersonalChallenge.objects.filter(profile=profile,cadence=cadence,period=period).exists():return False
    kind=('mine','hunt')[(period.toordinal()+profile.pk+(cadence=='weekly'))%2]
    count=(2 if cadence=='daily' else 6)+min(3,profile.level//10)
    return PersonalChallenge.objects.create(profile=profile,cadence=cadence,period=period,camp=profile.camp,kind=kind,required=count,ore=20 if cadence=='daily' else 60,experience=100 if cadence=='daily' else 400,premium=1 if cadence=='daily' else 2,reputation=5 if cadence=='daily' else 15)


def record_personal_event(profile,kind):
    if kind not in {'mine','hunt','raid','craft'}:return
    for challenge in PersonalChallenge.objects.select_for_update().filter(profile=profile,kind=kind,claimed_at__isnull=True):
        if challenge.period==period_for(challenge.cadence) and challenge.progress<challenge.required:
            challenge.progress+=1;challenge.save(update_fields=['progress'])
    for key,(_,event,count) in ACHIEVEMENTS.items():
        if event!=kind:continue
        award,_=PlayerAchievement.objects.select_for_update().get_or_create(profile=profile,key=key)
        if award.completed_at:continue
        award.progress=min(count,award.progress+1)
        if award.progress==count:award.completed_at=timezone.now()
        award.save(update_fields=['progress','completed_at'])


@player_action
def claim_challenge(profile,challenge_id):
    challenge=PersonalChallenge.objects.select_for_update().filter(pk=challenge_id,profile=profile).first()
    if not challenge or challenge.claimed_at or challenge.progress<challenge.required:return False
    # Ready goals remain claimable after the boundary; unfinished old goals stop progressing.
    profile.ore_balance+=challenge.ore;profile.experience+=challenge.experience
    from .economy import change_premium
    change_premium(profile,challenge.premium,'Wyzwanie osobiste',f'challenge:{challenge.pk}')
    if challenge.camp in {'OLD_CAMP','NEW_CAMP','SWAMP_CAMP'}:
        rep,_=CampReputation.objects.select_for_update().get_or_create(profile=profile,camp=challenge.camp)
        rep.value+=challenge.reputation;rep.save(update_fields=['value'])
    check_level_up(profile);profile.save();challenge.claimed_at=timezone.now();challenge.save(update_fields=['claimed_at']);return True


@player_action
def claim_achievement(profile,key):
    if key not in ACHIEVEMENTS:return False
    award=PlayerAchievement.objects.select_for_update().filter(profile=profile,key=key,completed_at__isnull=False,claimed_at__isnull=True).first()
    if not award:return False
    profile.ore_balance+=20
    from .economy import change_premium
    change_premium(profile,1,'Osiągnięcie: '+ACHIEVEMENTS[key][0],f'achievement:{award.pk}')
    profile.save();award.claimed_at=timezone.now();award.save(update_fields=['claimed_at']);return True


def cards(profile):
    rows=list(profile.challenges.filter(claimed_at__isnull=True).order_by('-period')[:20])
    current={row.cadence for row in rows if row.period==period_for(row.cadence)}
    # Claimed current goals must not advertise a second acceptance.
    for cadence in ('daily','weekly'):
        if profile.challenges.filter(cadence=cadence,period=period_for(cadence)).exists():current.add(cadence)
    return {'rows':[{'challenge':row,'label':'Odbierz urobek z kopalni' if row.kind=='mine' else 'Wygraj polowania na dostępnych terenach','ready':row.progress>=row.required,'expired':row.period!=period_for(row.cadence)} for row in rows],
        'daily_available':'daily' not in current,'weekly_available':'weekly' not in current,
        'achievements':[{'key':key,'name':name,'required':count,'award':profile.achievements.filter(key=key).first()} for key,(name,_,count) in ACHIEVEMENTS.items()],
        'reputation':CampReputation.objects.filter(profile=profile)}


def bot_personal_plan(profile):
    ready=profile.challenges.filter(claimed_at__isnull=True).order_by('pk')
    for challenge in ready:
        if challenge.progress>=challenge.required:return 'challenge_claim',challenge.pk
    award=profile.achievements.filter(completed_at__isnull=False,claimed_at__isnull=True).first()
    if award:return 'achievement_claim',list(ACHIEVEMENTS).index(award.key)+1
    if profile.bot_turn and profile.bot_turn%19==0:
        for n,cadence in enumerate(('daily','weekly'),1):
            if not profile.challenges.filter(cadence=cadence,period=period_for(cadence)).exists():return 'challenge_accept',n
    return '',None
