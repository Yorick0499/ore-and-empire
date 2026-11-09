"""Stable play styles, Polish wall-clock sessions and audited simulated purchases."""
from dataclasses import dataclass
from datetime import timedelta, timezone as utc
from hashlib import sha256
from django.utils import timezone
from .world_clock import POLISH_TIME

@dataclass(frozen=True)
class Persona:
    name: str
    windows: tuple
    cadence: int
    purchase_chance: int
    amount: tuple
    daily_cap: int
    shop_chance: int

PERSONAS={
 'grinder':Persona('Grinder',((0,720),),15,12,(2,5),10,12),
 'casual':Persona('Casual',((0,45),(285,75)),90,4,(1,3),4,8),
 'prospector':Persona('Poszukiwacz rudy',((0,180),(660,180)),30,3,(1,3),3,8),
 'merchant':Persona('Kupiec',((0,240),(600,240)),45,10,(2,4),8,15),
 'adventurer':Persona('Odkrywca',((0,120),(600,120)),45,8,(1,4),6,12),
 'social':Persona('Bywalec karczmy',((0,180),),120,5,(1,3),4,10),
 'patron':Persona('Gracz itemshopu',((0,180),(600,180)),30,85,(6,10),24,80),
}
CHOICES=tuple((key,p.name) for key,p in PERSONAS.items())
DISTRIBUTION=('grinder','grinder','grinder','casual','casual','casual','prospector','merchant','merchant','adventurer','social','patron')
def number(*parts):return int(sha256(':'.join(map(str,parts)).encode()).hexdigest()[:16],16)
def assignment(pk,world_id):return DISTRIBUTION[number('persona',world_id,pk)%len(DISTRIBUTION)],number('session',world_id,pk)%96*15
def persona(p):return PERSONAS.get(p.bot_personality,PERSONAS[assignment(p.pk,p.world_id)[0]])
def in_session(p,now=None):
    local=(now or timezone.now()).astimezone(POLISH_TIME)
    shift=p.bot_session_shift if p.bot_personality else assignment(p.pk,p.world_id)[1]
    minute=(local.hour*60+local.minute-shift)%1440
    return any(start<=minute<start+duration for start,duration in persona(p).windows)
def due(p,now=None):
    now=now or timezone.now()
    return (not p.world.bot_personality_cycles or in_session(p,now)) and (not p.bot_last_tick or now-p.bot_last_tick>=timedelta(seconds=persona(p).cadence))
def cycle_state(p,now=None):
    now=(now or timezone.now()).astimezone(utc.utc);definition=persona(p)
    online=in_session(p,now) if p.world.bot_personality_cycles else True
    result={'online':online,'name':definition.name,'hours':sum(d for _,d in definition.windows)/60,'cadence':definition.cadence}
    if p.world.bot_personality_cycles:
        base=now.replace(minute=now.minute//15*15,second=0,microsecond=0)
        for step in range(1,193):
            candidate=base+timedelta(minutes=15*step)
            if in_session(p,candidate)!=online:result['next']=candidate;break
    return result

def purchase_roll(p,now=None):
    local=(now or timezone.now()).astimezone(POLISH_TIME);definition=persona(p)
    reference=f'bot-topup:{p.world_id}:{p.pk}:{local.date()}:{local.hour//6}'
    n=number(reference)
    return (definition.amount[0]+n%(definition.amount[1]-definition.amount[0]+1) if n//100%100<definition.purchase_chance else 0),reference

def simulate_purchase(profile):
    from .game_logic import player_action
    from .economy import change_premium
    from .models import PremiumEntry
    from django.db.models import Sum
    @player_action
    def simulated_purchase(p):
        if not p.is_bot or not p.world.bot_simulated_purchases or not due(p):return 0
        amount,reference=purchase_roll(p)
        if not amount or PremiumEntry.objects.filter(reference=reference).exists():return 0
        used=PremiumEntry.objects.filter(profile=p,reference__startswith=reference.rsplit(':',1)[0]+':').aggregate(n=Sum('amount'))['n'] or 0
        amount=min(amount,max(0,persona(p).daily_cap-used))
        if amount:change_premium(p,amount,'Symulowany zakup odłamków bota',reference)
        return amount
    return simulated_purchase(profile)


def due_population(world):
    from .models import PlayerProfile
    people=PlayerProfile.objects.filter(world=world,is_bot=True,user__is_active=True).order_by('pk').only('pk','world_id','bot_personality','bot_session_shift','bot_last_tick')[:world.bot_count]
    now=timezone.now();ids=[]
    for p in people:
        p.world=world
        if due(p,now):ids.append(p.pk)
    return ids
