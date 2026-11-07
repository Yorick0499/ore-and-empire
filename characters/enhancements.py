"""Guaranteed improvements of individual items; shared by humans and bots."""
from uuid import UUID
from .game_logic import player_action
from .models import EquipmentWork, ItemBluePrint

DUST_KEY = 'rune-dust'
MAX_UPGRADE = 10
QUALITY_RANKS = (
    {'key':'ordinary','name':'Zwykły','ore':0,'dust':0},
    {'key':'reforged','name':'Wykuty na nowo','ore':60,'dust':3},
    {'key':'ore-forged','name':'Hartowany rudą','ore':300,'dust':10},
    {'key':'runic','name':'Runiczny','ore':1200,'dust':20},
    {'key':'enchanted','name':'Nasycony magią','ore':3600,'dust':30},
    {'key':'barrier-marked','name':'Naznaczony Barierą','ore':6390,'dust':47},
)
STAT_FIELDS = ('damage','weapon_prot','arrow_prot','fire_prot','magic_prot','strength_bonus','dexterity_bonus','mana_bonus','life_bonus')


def effective_stats(item):
    # Keep the historical power counter intact: existing equipment never loses stats.
    return {key: value + max(item.upgrade_level, value * item.upgrade_level // 20) if value else 0
            for key in STAT_FIELDS for value in [getattr(item.blueprint,key)]}


def upgrade_cost(item):
    rank = (item.upgrade_level + 1)//2 + 1
    if rank >= len(QUALITY_RANKS) or not item.blueprint.equippable or item.quantity != 1:
        return None
    return {**QUALITY_RANKS[rank], 'level':rank*2}


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
    item.upgrade_level=cost['level'];item.save(update_fields=['upgrade_level'])
    return EquipmentWork.objects.create(profile=profile,request_key=key,item_id_snapshot=item.pk,action='improve',snapshot={**cost,'name':item.display_name,'quality':item.quality_name,'tempering_version':2})


@player_action
def salvage_item(profile,item_id,key):
    prior,key=request(profile,item_id,key,'salvage')
    if prior is not None:return prior
    if key is None or profile.is_busy:return False
    item=profile.inventory.select_for_update().select_related('blueprint').filter(pk=item_id,is_equipped=False,is_market_listed=False,quantity=1).first()
    dust=ItemBluePrint.objects.filter(catalog_key=DUST_KEY).first()
    if not item or not item.can_salvage or not dust:return False
    amount=2+item.blueprint.min_level//5+item.upgrade_level
    name=item.display_name
    from .market_policy import record_market_event
    record_market_event(profile,item,'craft_input',quantity=1)
    item.delete()
    from .equipment import add_item
    add_item(profile,dust,amount)
    return EquipmentWork.objects.create(profile=profile,request_key=key,item_id_snapshot=item_id,action='salvage',snapshot={'name':name,'dust':amount})
