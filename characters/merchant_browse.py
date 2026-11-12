from .barrier import source_games
"""Player-facing catalog filters without changing the purchase rules."""
from .text_search import literal_pattern
from .models import ItemBluePrint
from .market_browse import bounded_page,pager


def merchant_context(profile,params):
    kinds=[(key,ItemBluePrint(kind=key).kind_name) for key,_ in ItemBluePrint._meta.get_field('kind').choices]
    weapons={'onehand':'Jednoręczna','twohand':'Dwuręczna','bow':'Łuk','crossbow':'Kusza'}
    filters={'q':params.get('q','').strip()[:100],
             'kind':params.get('kind','') if params.get('kind') in dict(kinds) else '',
             'weapon':params.get('weapon','') if params.get('weapon') in weapons else '',
             'affordable':'1' if params.get('affordable')=='1' else '',
             'usable':'1' if params.get('usable')=='1' else ''}
    stock=ItemBluePrint.objects.filter(source_game__in=source_games(profile),merchant=True,base_value__gte=0,min_level__lte=profile.level,
        required_camp__in=['',profile.camp],min_camp_tier__lte=profile.camp_tier)
    from .jarkendar import unlocked
    if not unlocked(profile):stock=stock.exclude(catalog_key__startswith='oe-jark-')
    if filters['q']:stock=stock.filter(name__iregex=literal_pattern(filters['q']))
    if filters['kind']:stock=stock.filter(kind=filters['kind'])
    if filters['weapon']:stock=stock.filter(kind='weapon',weapon_type=filters['weapon'])
    if filters['affordable']:stock=stock.filter(base_value__lte=profile.ore_balance)
    if filters['usable']:stock=stock.exclude(kind__in=['weapon','armor','ring','amulet'],required_strength__gt=profile.strength).exclude(kind__in=['weapon','armor','ring','amulet'],required_dexterity__gt=profile.dexterity)
    stock=bounded_page(stock.order_by('base_value','name','pk'),params,'page')
    bag=bounded_page(profile.inventory.filter(is_equipped=False,is_market_listed=False,is_protected=False,blueprint__tradeable=True)
        .exclude(pk=profile.prepared_magic_id).select_related('blueprint').order_by('blueprint__name','pk'),params,'bag_page')
    for item in stock:
        item.purchase_affordable=profile.ore_balance>=item.base_value
        item.equipment_ready=not item.equippable or (profile.strength>=item.required_strength and profile.dexterity>=item.required_dexterity)
    canonical={**filters,'page':stock.number,'bag_page':bag.number}
    return {'shop_items':stock,'player_inventory':bag,'merchant_filters':filters,'item_kinds':kinds,'weapon_types':weapons.items(),
            'stock_pager':pager(stock,'page',canonical,'Strony kupca'),'bag_pager':pager(bag,'bag_page',canonical,'Strony sprzedaży kupcowi')}
