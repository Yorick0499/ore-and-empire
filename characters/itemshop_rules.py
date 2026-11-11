"""Shared Polish-day purchase caps and useful, personality-aware choices."""
from datetime import datetime,time,timedelta
from django.db.models import Count
from django.utils import timezone
from .world_clock import POLISH_TIME
from .models import StorePurchase
LIMITS={'mana':5,'xp':3,'weapon':2,'item':2}
def unavailable_reason(p,q,energy_left,limits=None):
    """The same eligibility decision serves the purchase, bots and visible UI."""
    if q.blueprint and q.blueprint.source_game not in {'adaptation',p.world.universe}:return 'Przedmiot pochodzi z innego świata.'
    if not q.enabled:return 'Oferta jest wyłączona.'
    if p.level<q.level:return f'Wymagany poziom: {q.level}.'
    if q.kind in LIMITS and not (limits if limits is not None else remaining(p))[q.kind]:return 'Wykorzystano limit zakupów na dziś (czas polski).'
    if q.kind=='energy' and energy_left<=0:return 'Wykorzystano limit odnowień energii na dziś (czas polski).'
    if q.kind in {'energy','health','mana'}:
        if q.effect<=0:return 'Oferta nie ma aktywnego efektu.'
        if getattr(p,'current_'+q.kind)>=getattr(p,'max_'+q.kind):return {'energy':'Masz pełną energię.','health':'Masz pełne zdrowie.','mana':'Masz pełną manę.'}[q.kind]
    elif q.kind=='xp':
        if not 1<=q.effect<=300:return 'Oferta nie ma aktywnego efektu.'
    elif q.kind=='weapon':
        if not q.blueprint or not q.blueprint.equippable:return 'Brak dostępnego sprzętu.'
    elif q.kind=='item':
        if not q.blueprint or q.blueprint.equippable or not 1<=q.effect<=100:return 'Brak dostępnego materiału.'
    else:return 'Nieznany rodzaj oferty.'
    if p.premium_balance<q.price:return f'Brakuje {q.price-p.premium_balance} odłamków. Zdobędziesz je za zlecenia.'
    return ''

def remaining(p):
    start=datetime.combine(timezone.now().astimezone(POLISH_TIME).date(),time(),tzinfo=POLISH_TIME)
    used={r['kind_snapshot']:r['n'] for r in StorePurchase.objects.filter(profile=p,created_at__gte=start,created_at__lt=start+timedelta(days=1)).values('kind_snapshot').annotate(n=Count('pk'))}
    return {kind:max(0,limit-used.get(kind,0)) for kind,limit in LIMITS.items()}
def helpful(p,q,energy_left,limits=None):
    return not unavailable_reason(p,q,energy_left,limits)

def choose(p,items,products,energy_left):
    from .market_intelligence import score,usable,fists
    from .bot_personalities import persona,number
    candidates=[];limits=remaining(p)
    held=[i for i in items if not i.is_market_listed]
    for q in products:
        if not helpful(p,q,energy_left,limits):continue
        priority=0;gain=0
        if q.kind=='health' and p.current_health<p.max_health-20:
            priority=100 if p.current_health<10 else 30;gain=min(q.effect,p.max_health-p.current_health)
        elif q.kind=='energy' and p.current_energy<p.max_energy//2:
            priority=100 if p.current_energy<15 else 25;gain=min(q.effect,p.max_energy-p.current_energy)
        elif q.kind=='mana' and p.prepared_magic_id and p.current_mana<p.max_mana//2:
            priority=90 if p.current_mana<4 else 25;gain=min(q.effect,p.max_mana-p.current_mana)
        elif q.kind=='xp':priority=10;gain=q.effect//10
        elif q.kind=='weapon' and usable(p,q.blueprint):
            old=max((score(p,i) for i in held if i.blueprint.kind==q.blueprint.kind),default=fists(p) if q.blueprint.kind=='weapon' else 0)
            gain=score(p,q.blueprint)-old;priority=20 if gain>=3 else 0
        elif q.kind=='item' and q.blueprint.catalog_key=='rune-dust':
            dust=sum(i.quantity for i in held if i.blueprint_id==q.blueprint_id)
            if any(i.is_equipped and i.upgrade_cost and p.ore_balance>=i.upgrade_cost['ore']+20 and dust<i.upgrade_cost['dust'] for i in held):priority=15;gain=q.effect
        if priority:candidates.append((priority,gain/q.price,-q.pk,q))
    if not candidates:return None,False
    best=max(candidates,key=lambda r:r[:3]);urgent=best[0]>=90
    if not urgent and number('shop',p.pk,p.world_id,p.bot_turn)%100>=persona(p).shop_chance:return None,False
    return best[-1],urgent
