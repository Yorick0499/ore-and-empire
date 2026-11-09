"""Sell a common weapon only together with a guaranteed usable replacement."""
from django.db import transaction
from .models import PlayerProfile,OwnedItem,ItemBluePrint
from .market_intelligence import usable,score
from . import game_logic as game

def plan(p,inventory,stock):
    old=next((i for i in inventory if i.is_equipped and i.equipped_slot=='weapon'),None)
    if not old or old.is_protected or old.rarity or old.upgrade_level or not old.blueprint.tradeable:return None
    proceeds=old.blueprint.base_value//2*old.quantity;choices=[]
    for b in stock:
        if b.kind!='weapon' or not b.merchant or not usable(p,b):continue
        gain=score(p,b)-score(p,old)
        if gain>=max(5,score(p,old)//5) and p.ore_balance-20<b.base_value<=p.ore_balance+proceeds-20 and b.base_value<=gain*40:choices.append((b.base_value/gain,-gain,b.pk,b))
    return min(choices,key=lambda row:row[:3])[-1] if choices else None

class ReplacementUnavailable(Exception):pass

def finance(p,old_id,new_id,expected_price):
    try:
        with transaction.atomic():
            PlayerProfile.objects.select_for_update().get(pk=p.pk);p.refresh_from_db()
            old=OwnedItem.objects.select_for_update(of=('self',)).select_related('blueprint').filter(pk=old_id,owner=p,is_equipped=True,equipped_slot='weapon').first()
            if not old:return False
            blueprints={b.pk:b for b in ItemBluePrint.objects.select_for_update().filter(pk__in=[old.blueprint_id,new_id]).order_by('pk')}
            b=blueprints.get(new_id);old.blueprint=blueprints[old.blueprint_id]
            if not p.is_bot or p.is_busy or not b or type(expected_price)is not int or b.base_value!=expected_price or not plan(p,[old],[b]):return False
            if not game.unequip_item(p,old):raise ReplacementUnavailable()
            if not game.sell_item_from_npc(p,old):raise ReplacementUnavailable()
            if not game.buy_item_from_npc(p,b):raise ReplacementUnavailable()
            new=p.inventory.filter(blueprint=b,is_equipped=False,is_market_listed=False).order_by('-pk').first()
            if not new or not game.equip_item(p,new):raise ReplacementUnavailable()
            return True
    except ReplacementUnavailable:
        p.refresh_from_db()
        if hasattr(p,'_gear_stats_cache'):del p._gear_stats_cache
        return False
