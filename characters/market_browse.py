"""Bounded market pages; filters affect browsing, never trading permissions."""
from urllib.parse import urlencode
from django.core.paginator import Paginator
from django.db.models import ExpressionWrapper, F, FloatField
from django.db.models.functions import Cast
from .enhancements import QUALITY_RANKS
from .game_logic import MAX_MARKET_PRICE
from .models import ItemBluePrint, OwnedItem

PAGE_SIZE = 24
ORDERINGS = {
    'newest': (F('listed_at').desc(nulls_last=True), '-pk'),
    'price': ('market_price', 'pk'),
    'price-desc': ('-market_price', 'pk'),
    'unit': ('unit_price', 'pk'),
}


def bounded_page(queryset, params, key):
    raw = params.get(key, '1')
    return Paginator(queryset, PAGE_SIZE).get_page(raw[:10])


def pager(page, key, params, label):
    def link(number):
        return '?' + urlencode({**params, key: number})
    return {'page':page, 'label':label,
            'previous_url':link(page.previous_page_number()) if page.has_previous() else '',
            'next_url':link(page.next_page_number()) if page.has_next() else ''}


def browse_market(profile, params):
    kinds = [(key, ItemBluePrint(kind=key).kind_name) for key, _ in ItemBluePrint._meta.get_field('kind').choices]
    filters = {
        'q': params.get('q', '').strip()[:100],
        'kind': params.get('kind', '') if params.get('kind') in dict(kinds) else '',
        'quality': params.get('quality', '') if params.get('quality') in {r['key'] for r in QUALITY_RANKS} else '',
        'seller': params.get('seller', '') if params.get('seller') in {'mine', 'others'} else '',
        'sort': params.get('sort', 'newest') if params.get('sort', 'newest') in ORDERINGS else 'newest',
        'max_price': '',
    }
    price = params.get('max_price', '').strip()
    error = ''
    if price:
        if price.isascii() and price.isdecimal() and len(price) <= 7 and 1 <= int(price) <= MAX_MARKET_PRICE:
            filters['max_price'] = str(int(price))
        else:
            error = 'Maksymalna cena musi wynosić od 1 do 1000000 rudy. Pominięto ten filtr.'
    # Joining the owner's user prevents one query per displayed seller's name.
    all_offers = OwnedItem.objects.filter(owner__world_id=profile.world_id, is_market_listed=True).select_related('blueprint', 'owner__user')
    offers = all_offers
    if filters['q']:
        offers = offers.filter(blueprint__name__icontains=filters['q'])
    if filters['kind']:
        offers = offers.filter(blueprint__kind=filters['kind'])
    if filters['quality']:
        rank = next(i for i, r in enumerate(QUALITY_RANKS) if r['key'] == filters['quality'])
        offers = offers.filter(rarity=rank)
    if filters['seller'] == 'mine':
        offers = offers.filter(owner=profile)
    elif filters['seller'] == 'others':
        offers = offers.exclude(owner=profile)
    if filters['max_price']:
        offers = offers.filter(market_price__lte=int(filters['max_price']))
    offers = offers.annotate(unit_price=ExpressionWrapper(Cast(F('market_price'), FloatField()) / F('quantity'), output_field=FloatField()))
    offers = bounded_page(offers.order_by(*ORDERINGS[filters['sort']]), params, 'page')
    own = bounded_page(all_offers.filter(owner=profile).order_by(F('listed_at').desc(nulls_last=True), '-pk'), params, 'own_page')
    bag = bounded_page(profile.inventory.filter(is_equipped=False, is_market_listed=False, is_protected=False,
        blueprint__tradeable=True).exclude(pk=profile.prepared_magic_id).select_related('blueprint').order_by('blueprint__name','pk'), params, 'bag_page')
    canonical = {**filters, 'page':offers.number, 'own_page':own.number, 'bag_page':bag.number}
    return {'market_all_items':offers, 'my_offers':own, 'player_inventory':bag,
            'market_filters':filters, 'filter_error':error, 'item_kinds':kinds, 'all_quality_ranks':QUALITY_RANKS,
            'offers_pager':pager(offers, 'page', canonical, 'Strony ofert'),
            'own_pager':pager(own, 'own_page', canonical, 'Strony twoich ogłoszeń'),
            'bag_pager':pager(bag, 'bag_page', canonical, 'Strony plecaka na targu')}
