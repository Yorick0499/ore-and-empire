"""Guaranteed improvements of individual items; shared by humans and bots."""
from uuid import UUID
from .game_logic import player_action
from .models import EquipmentWork, ItemBluePrint

DUST_KEY = 'rune-dust'
MAX_UPGRADE = 10
STAT_FIELDS = ('damage','weapon_prot','arrow_prot','fire_prot','magic_prot','strength_bonus','dexterity_bonus','mana_bonus','life_bonus')


def effective_stats(item):
    # Base catalog is immutable. A +10 item has +50% of its own non-zero stats.
    return {key: value + max(item.upgrade_level, value * item.upgrade_level // 20) if value else 0
            for key in STAT_FIELDS for value in [getattr(item.blueprint,key)]}


def upgrade_cost(item):
    n = item.upgrade_level + 1
    return {'level':n,'ore':30*n*n,'dust':2*n} if n <= MAX_UPGRADE and item.blueprint.equippable and item.quantity == 1 else None


def request(profile, item_id, key, action):
    try:key = UUID(str(key))
    except (ValueError,TypeError,AttributeError):return None, None
    prior = EquipmentWork.objects.filter(profile=profile,request_key=key).first()
    if prior:return prior if prior.item_id_snapshot == item_id and prior.action == action else False, key
    return None, key


@player_action
def improve_item(profile,item_id,expected_level,key):
    prior,key = request(profile,item_id,key,'improve')
    if prior is not None:return prior
    if key is None or type(expected_level) is not int:return False
    item = profile.inventory.select_for_update().select_related('blueprint').filter(pk=item_id,is_market_listed=False).first()
    if not item or item.upgrade_level != expected_level or profile.is_busy:return False
    cost = upgrade_cost(item)
    if not cost or profile.ore_balance < cost['ore']:return False
    dust = profile.inventory.select_for_update().filter(blueprint__catalog_key=DUST_KEY,is_market_listed=False,is_equipped=False).order_by('pk')
    stacks=list(dust)
    if sum(i.quantity for i in stacks) < cost['dust']:return False
    remaining=cost['dust']
    from .market_policy import record_market_event
    for stack in stacks:
        amount=min(remaining,stack.quantity)
        if not amount:break
        record_market_event(profile,stack,'craft_input',quantity=amount)
        if stack.quantity==amount:stack.delete()
        else:stack.quantity-=amount;stack.save(update_fields=['quantity'])
        remaining-=amount
    profile.ore_balance-=cost['ore'];profile.save(update_fields=['ore_balance'])
    item.upgrade_level+=1;item.save(update_fields=['upgrade_level'])
    return EquipmentWork.objects.create(profile=profile,request_key=key,item_id_snapshot=item.pk,action='improve',snapshot={'name':item.display_name,**cost})


@player_action
def salvage_item(profile,item_id,key):
    prior,key=request(profile,item_id,key,'salvage')
    if prior is not None:return prior
    if key is None or profile.is_busy:return False
    item=profile.inventory.select_for_update().select_related('blueprint').filter(pk=item_id,is_equipped=False,is_market_listed=False,quantity=1,blueprint__catalog_key__startswith='colony-loot-').first()
    dust=ItemBluePrint.objects.filter(catalog_key=DUST_KEY).first()
    if not item or not dust:return False
    amount=2+item.blueprint.min_level//5+item.upgrade_level
    name=item.display_name
    from .market_policy import record_market_event
    record_market_event(profile,item,'craft_input',quantity=1)
    item.delete()
    from .equipment import add_item
    add_item(profile,dust,amount)
    return EquipmentWork.objects.create(profile=profile,request_key=key,item_id_snapshot=item_id,action='salvage',snapshot={'name':name,'dust':amount})
