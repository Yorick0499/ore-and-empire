"""Currency movement facts: transfers and operator edits are not minted rewards."""
from uuid import uuid4
from .world_clock import POLISH_TIME
from datetime import datetime,time,timedelta,timezone as utc
from django.db.models import Sum,Avg,Count,Min
from django.utils import timezone
from .models import EconomicEntry,PlayerProfile,MarketTrade,EnergyRefill,ItemBluePrint

RESOURCE_FIELDS={'ore':'ore_balance','shards':'premium_balance'}
REFILLS_PER_DAY=5


def balances(ids):
    return {p.pk:{r:getattr(p,field) for r,field in RESOURCE_FIELDS.items()} for p in PlayerProfile.objects.filter(pk__in=ids)}


def record_changes(before,operation,category=None):
    reference=uuid4()
    for pk,after in balances(before).items():
        for resource,value in after.items():
            amount=value-before[pk][resource]
            if not amount:continue
            kind=category or ('transfer' if operation=='buy_item_on_market' else 'source' if amount>0 else 'sink')
            EconomicEntry.objects.create(profile_id=pk,resource=resource,amount=amount,balance_after=value,category=kind,operation=operation,reference=reference,created_at=timezone.now())


def record_opening(profile):
    for resource,field in RESOURCE_FIELDS.items():
        value=getattr(profile,field)
        if value:
            EconomicEntry.objects.create(profile=profile,resource=resource,amount=value,balance_after=value,category='opening',operation='account_created',reference=uuid4())


def refills_remaining(profile,now=None):
    now=now or timezone.now()
    start=datetime.combine(now.astimezone(POLISH_TIME).date(),time(),tzinfo=POLISH_TIME)
    return max(0,REFILLS_PER_DAY-EnergyRefill.objects.filter(profile=profile,created_at__gte=start,created_at__lt=start+timedelta(days=1)).count())


def summary():
    from .worlds import current_world
    world=current_world()
    totals={resource:{category:0 for category in ('opening','source','sink','transfer','admin')} for resource in RESOURCE_FIELDS}
    for row in EconomicEntry.objects.filter(profile__world=world).values('resource','category').annotate(total=Sum('amount')):
        totals[row['resource']][row['category']]=row['total']
    for resource,field in RESOURCE_FIELDS.items():
        actual=PlayerProfile.objects.filter(world=world).aggregate(total=Sum(field))['total'] or 0
        totals[resource]['actual_balance']=actual
        totals[resource]['reconciliation_gap']=actual-sum(totals[resource][c] for c in ('opening','source','sink','transfer','admin'))
    since=EconomicEntry.objects.filter(profile__world=world).aggregate(first=Min('created_at'))['first']
    trades=MarketTrade.objects.filter(seller__world=world,created_at__gte=since) if since else MarketTrade.objects.none()
    averages={r['blueprint_id']:r for r in trades.filter(blueprint__kind='weapon').values('blueprint_id').annotate(average=Avg('price'),count=Count('pk'))}
    prices=[]
    for item in ItemBluePrint.objects.filter(merchant=True,kind='weapon').order_by('base_value','pk')[:30]:
        market=averages.get(item.pk,{})
        prices.append({'name':item.name,'npc':item.base_value,'g1':item.original_stats.get('value'),'market_average':round(market['average'],2) if market else None,'trades':market.get('count',0)})
    return {'simulated_purchase_shards':EconomicEntry.objects.filter(profile__world=world,operation='simulated_purchase',resource='shards').aggregate(n=Sum('amount'))['n'] or 0,'resources':totals,'market_turnover':trades.aggregate(total=Sum('price'))['total'] or 0,'since':since.isoformat() if since else None,'prices':prices,'refills_per_day':REFILLS_PER_DAY,'entries':EconomicEntry.objects.count()}
