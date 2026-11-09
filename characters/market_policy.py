"""Observed prices, bounded budgets and disposal of unsold stock; no balance setters."""
from datetime import timedelta
from statistics import median
from django.db.models import Sum,Count
from django.utils import timezone
from .models import MarketEvent,MarketTrade,OwnedItem
from .game_logic import player_action,MAX_MARKET_PRICE


def record_market_event(profile,item,action,price=0,quantity=None,reason=''):
    from .market_intelligence import invalidate
    invalidate(profile.world_id)
    return MarketEvent.objects.create(created_at=timezone.now(),profile=profile,item=item,blueprint_id=item.blueprint_id,action=action,price=max(0,price or 0),quantity=quantity or item.quantity,reason=reason)


def reference_price(blueprint,world_id):
    rows=MarketTrade.objects.filter(blueprint=blueprint,seller__world_id=world_id,quantity__gt=0).order_by('-created_at','-pk').values_list('price','quantity')[:20]
    observed=median([price/quantity for price,quantity in rows]) if rows else blueprint.base_value
    return max(1,round(max(blueprint.base_value*.6,min(blueprint.base_value*1.4,observed))))


def listing_price(profile,item):
    from .market_intelligence import state
    return state(profile.world_id).quote(profile,item).price


@player_action
def reprice_listing(profile,item,price,expected_price):
    if item.owner_id!=profile.pk or not item.is_market_listed or item.market_price!=expected_price or type(price)is not int or not 1<=price<=MAX_MARKET_PRICE or price==item.market_price:return False
    item.market_price=price;item.save(update_fields=['market_price'])
    record_market_event(profile,item,'repricing',price,reason='stale');return True


@player_action
def observe_legacy_listing(profile,item):
    if item.owner_id!=profile.pk or not item.is_market_listed or item.listed_at is not None:return False
    if not MarketEvent.objects.filter(profile=profile,item=item,action='legacy_observation').exists():record_market_event(profile,item,'legacy_observation',item.market_price,reason='unknown_age')
    return True


def bot_market_plan(profile,reserved=(),inventory=None,market=None):
    from .market_intelligence import state,retention
    now=timezone.now();inventory=inventory if inventory is not None else list(profile.inventory.select_related('blueprint'))
    market=market or state(profile.world_id);keep=retention(profile,inventory,reserved)
    for item in inventory:
        if not item.is_market_listed:continue
        if item.pk in keep:return 'market_cancel',item.pk,0
        start=item.listed_at
        if start is None:
            observed=MarketEvent.objects.filter(profile=profile,item=item,action='legacy_observation').order_by('pk').first()
            if not observed:return 'market_observe',item.pk,0
            start=observed.created_at
        quote=market.quote(profile,item)
        if start<=now-timedelta(days=3) or not quote.price:return 'market_cancel',item.pk,0
        price=quote.price
        if start<=now-timedelta(days=1):price=max(item.blueprint.base_value*item.quantity//2+1,min(price,item.market_price*85//100))
        if abs(price-item.market_price)>=max(2,item.market_price//10) and not MarketEvent.objects.filter(item=item,action='repricing',created_at__gte=now-timedelta(hours=6)).exists():return 'market_reprice',item.pk,price
    cancelled=MarketEvent.objects.filter(profile=profile,action='cancellation',reason='stale',item__isnull=False,item__is_market_listed=False,item__is_equipped=False,item__is_protected=False).exclude(blueprint_id__in=reserved).select_related('item__blueprint').first()
    if cancelled and cancelled.item.owner_id==profile.pk and cancelled.item_id not in keep and cancelled.item.blueprint.tradeable:return 'market_sell',cancelled.item_id,0
    if len(inventory)>=12:return '',None,0
    candidates=[]
    for item in market.listings:
        if item.owner_id==profile.pk or item.blueprint.kind=='weapon' or market.need(profile,item)<item.quantity:continue
        quote=market.quote(item.owner,item)
        if quote.price and item.market_price<=min(quote.price,profile.ore_balance-20):candidates.append(item)
    if candidates:
        best=min(candidates,key=lambda i:(i.market_price/i.quantity,i.pk));return 'market_buy',best.pk,best.market_price
    return '',None,0


@player_action
def list_bot_surplus(profile,item,reserved=()):
    from .market_intelligence import state,sale_candidate
    inventory=list(profile.inventory.select_related('blueprint'));market=state(profile.world_id,fresh=True)
    candidate=sale_candidate(profile,inventory,reserved,market)
    if not candidate or candidate.pk!=item.pk:return False
    from .game_logic import list_item_on_market
    return list_item_on_market(profile,candidate,market.quote(profile,candidate).price)


def market_effectiveness(world):
    trades=MarketTrade.objects.filter(seller__world=world)
    events=MarketEvent.objects.filter(profile__world=world)
    return {'trades':trades.count(),'bot_turnover':trades.filter(seller__is_bot=True,buyer__is_bot=True).aggregate(total=Sum('price'))['total'] or 0,
        'listed':events.filter(action='listing').count(),'cancelled':events.filter(action='cancellation').count(),'repriced':events.filter(action='repricing').count(),
        'used_units':events.filter(action__in=['consumption','craft_input']).aggregate(total=Sum('quantity'))['total'] or 0,
        'age_unknown':OwnedItem.objects.filter(owner__world=world,is_market_listed=True,listed_at__isnull=True).count()}
