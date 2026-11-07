"""Observed prices, bounded budgets and disposal of unsold stock; no balance setters."""
from datetime import timedelta
from statistics import median
from django.db.models import Sum,Count
from django.utils import timezone
from .models import MarketEvent,MarketTrade,OwnedItem
from .game_logic import player_action,MAX_MARKET_PRICE


def record_market_event(profile,item,action,price=0,quantity=None,reason=''):
    return MarketEvent.objects.create(profile=profile,item=item,blueprint_id=item.blueprint_id,action=action,price=max(0,price or 0),quantity=quantity or item.quantity,reason=reason)


def reference_price(blueprint,world_id):
    rows=MarketTrade.objects.filter(blueprint=blueprint,seller__world_id=world_id,quantity__gt=0).order_by('-created_at','-pk').values_list('price','quantity')[:20]
    observed=median([price/quantity for price,quantity in rows]) if rows else blueprint.base_value
    return max(1,round(max(blueprint.base_value*.6,min(blueprint.base_value*1.4,observed))))


def listing_price(profile,item):
    unit=reference_price(item.blueprint,profile.world_id)
    return min(MAX_MARKET_PRICE,max(1,round(unit*item.quantity*1.05)))


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


def bot_market_plan(profile,reserved=()):
    now=timezone.now()
    stale=profile.inventory.filter(is_market_listed=True,listed_at__lt=now-timedelta(days=1)).select_related('blueprint').order_by('listed_at','pk').first()
    age_start=stale.listed_at if stale else None
    if not stale:
        unknown=profile.inventory.filter(is_market_listed=True,listed_at__isnull=True).select_related('blueprint').order_by('pk').first()
        if unknown:
            observed=MarketEvent.objects.filter(profile=profile,item=unknown,action='legacy_observation').order_by('pk').first()
            if not observed:return 'market_observe',unknown.pk,0
            if observed.created_at<now-timedelta(days=1):stale=unknown;age_start=observed.created_at
    if stale:
        if age_start<=now-timedelta(days=3):return 'market_cancel',stale.pk,0
        floor=max(1,stale.blueprint.base_value*stale.quantity//2)
        if stale.market_price>floor and not MarketEvent.objects.filter(item=stale,action='repricing',created_at__gte=now-timedelta(days=1)).exists():
            return 'market_reprice',stale.pk,max(floor,stale.market_price*85//100)
    cancelled=MarketEvent.objects.filter(profile=profile,action='cancellation',reason='stale',item__isnull=False,item__is_market_listed=False,item__is_equipped=False,item__is_protected=False).exclude(blueprint_id__in=reserved).select_related('item__blueprint').first()
    if cancelled and cancelled.item.owner_id==profile.pk and cancelled.item.blueprint.tradeable and cancelled.item.pk!=profile.prepared_magic_id:return 'market_sell',cancelled.item_id,0
    if profile.inventory.count()>=6 or profile.ore_balance<25:return '',None,0
    offers=OwnedItem.objects.filter(owner__world_id=profile.world_id,is_market_listed=True,market_price__gt=0,market_price__lte=profile.ore_balance-20).exclude(owner=profile).select_related('blueprint')
    # Buy healing for actual injuries, not to pass the same goods to another bot.
    if profile.current_health<profile.max_health//2 and not profile.inventory.filter(blueprint__heal_amount__gt=0,is_market_listed=False).exists():
        health=list(offers.filter(blueprint__kind='consumable',blueprint__heal_amount__gt=0,quantity__lte=2))
        health=[o for o in health if o.market_price<=reference_price(o.blueprint,profile.world_id)*o.quantity*1.2]
        best=min(health,key=lambda o:o.market_price/(o.blueprint.heal_amount*o.quantity),default=None)
        if best:return 'market_buy',best.pk,0
    from .crafting import recipe_cards,interested
    for card in recipe_cards(profile):
        recipe=card['recipe']
        if not interested(profile,recipe) or getattr(profile,recipe.discipline+'_skill')<recipe.skill:continue
        for ingredient in card['ingredients']:
            needed=ingredient['need']-ingredient['have']
            if needed<=0:continue
            choices=list(offers.filter(blueprint=ingredient['blueprint'],quantity__lte=needed+2))
            choices=[o for o in choices if o.market_price<=reference_price(o.blueprint,profile.world_id)*o.quantity*1.2]
            best=min(choices,key=lambda o:(o.market_price/o.quantity,o.pk),default=None)
            if best:return 'market_buy',best.pk,0
    return '',None,0


def market_effectiveness(world):
    trades=MarketTrade.objects.filter(seller__world=world)
    events=MarketEvent.objects.filter(profile__world=world)
    return {'trades':trades.count(),'bot_turnover':trades.filter(seller__is_bot=True,buyer__is_bot=True).aggregate(total=Sum('price'))['total'] or 0,
        'listed':events.filter(action='listing').count(),'cancelled':events.filter(action='cancellation').count(),'repriced':events.filter(action='repricing').count(),
        'used_units':events.filter(action__in=['consumption','craft_input']).aggregate(total=Sum('quantity'))['total'] or 0,
        'age_unknown':OwnedItem.objects.filter(owner__world=world,is_market_listed=True,listed_at__isnull=True).count()}
