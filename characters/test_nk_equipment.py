from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from django.core.management import call_command
from django.test import TestCase,SimpleTestCase
from django.utils import timezone
from .test_faction_succession import fixture,person,succeed
from .models import ItemBluePrint,OwnedItem
from . import game_logic as game
from .equipment import compare_equipment

class NkEquipmentTests(TestCase):
    def setUp(self):
        self.c,self.i,self.race=fixture();call_command('seed_khorinis',stdout=StringIO());self.p=person(self.c,'OLD_CAMP','BARON');self.p.level=45;self.p.life=600;self.p.current_health=600;self.p.ore_balance=20000;self.p.mana=150;self.p.current_mana=150;self.p.save();succeed(self.race)
    def buy(self,key):
        bp=ItemBluePrint.objects.get(catalog_key=key);self.assertTrue(game.buy_item_from_npc(self.p,bp));return self.p.inventory.get(blueprint=bp)
    def test_belt_has_own_slot_and_six_reviewed_armor_sets_apply_once(self):
        armor=self.buy('g2nk-itar_leather_l');belt=self.buy('g2nk-itbe_addon_leather_01');self.assertTrue(game.equip_item(self.p,armor));before=self.p.equipment_stats.copy()
        comparison=compare_equipment(self.p,belt);wp=next(r for r in comparison['rows'] if r['label']=='Ochrona przed bronią');self.assertEqual(wp['delta'],10)
        self.assertTrue(game.equip_item(self.p,belt));belt.refresh_from_db();self.assertEqual(belt.equipped_slot,'belt');self.assertEqual(self.p.equipment_stats['weapon_prot'],before['weapon_prot']+10)
        other=self.buy('g2nk-itbe_addon_prot_edge');comparison=compare_equipment(self.p,other);wp=next(r for r in comparison['rows'] if r['label']=='Ochrona przed bronią');self.assertEqual(wp['delta'],0)
        fire=next(r for r in comparison['rows'] if r['label']=='Ochrona przed ogniem');self.assertEqual(fire['delta'],-5)
        self.assertTrue(game.equip_item(self.p,other));self.assertEqual(self.p.inventory.filter(is_equipped=True,equipped_slot='belt').count(),1)
        self.assertEqual(self.p.equipment_stats['fire_prot'],armor.blueprint.fire_prot)
        self.assertTrue(game.unequip_item(self.p,other));self.assertEqual(self.p.equipment_stats['weapon_prot'],before['weapon_prot'])
    def test_mana_and_health_restoration_consumes_one_unit_and_no_energy_refill(self):
        from .models import EnergyRefill
        potion=ItemBluePrint.objects.get(catalog_key='g2nk-itpo_mana_03');self.assertTrue(game.buy_item_from_npc(self.p,potion,2));owned=self.p.inventory.get(blueprint=potion)
        self.p.current_mana=0;self.p.save();self.assertTrue(game.use_item(self.p,owned));self.p.refresh_from_db();owned.refresh_from_db();self.assertEqual((self.p.current_mana,owned.quantity),(100,1))
        self.assertTrue(game.use_item(self.p,owned));self.p.refresh_from_db();self.assertEqual(self.p.current_mana,150);self.assertFalse(self.p.inventory.filter(pk=owned.pk).exists());self.assertFalse(EnergyRefill.objects.exists())
        hp=self.buy('g2nk-itpo_health_01');self.assertFalse(game.use_item(self.p,hp));self.assertTrue(self.p.inventory.filter(pk=hp.pk).exists())
        self.p.current_health=10;self.p.save();self.assertTrue(game.use_item(self.p,hp));self.p.refresh_from_db();self.assertEqual(self.p.current_health,60)
    def test_permanent_source_potions_cannot_grant_free_stats(self):
        bp=ItemBluePrint.objects.get(catalog_key='g2nk-itpo_perm_str');self.assertFalse(bp.merchant)
        item=OwnedItem.objects.create(owner=self.p,blueprint=bp);before=self.p.strength
        self.assertFalse(game.use_item(self.p,item));self.p.refresh_from_db();self.assertEqual(self.p.strength,before)
    def test_market_and_bot_keep_a_useful_mana_potion(self):
        from .market_intelligence import retention,MarketState
        potion=self.buy('g2nk-itpo_mana_03');self.p.current_mana=0;self.p.magic_skill=1;self.p.save()
        self.assertIn(potion.pk,retention(self.p,[potion]))
        seller=person(self.i,'CITY_WATCH','K2_COMMANDER');other=OwnedItem.objects.create(owner=seller,blueprint=potion.blueprint,is_market_listed=True,market_price=20)
        market=MarketState(self.c.pk);buyer=next(p for p in market.people if p.pk==self.p.pk)
        self.assertGreater(market.need(buyer,other),0)

class NkEffectParserTests(SimpleTestCase):
    def test_restoratives_are_bounded_and_never_parse_permanent_stats(self):
        from .gothic2_sources import restorative_effect
        self.assertEqual(restorative_effect({'Działanie':'Przywraca 50 punktów many'}),{'mana':50})
        self.assertEqual(restorative_effect({'Działanie':'Przywraca 100 % many'}),{'mana_percent':100})
        for text in ['+3 do siły na stałe','Przywraca 1000 % many','Przywraca -10 punktów many','Przemiana w smoka']:
            self.assertFalse(restorative_effect({'Działanie':text}))

from django.test import TransactionTestCase,skipUnlessDBFeature
class NkRestorationContentionTests(TransactionTestCase):
    @skipUnlessDBFeature('has_select_for_update')
    def test_one_mana_potion_cannot_restore_twice_in_two_workers(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        from .models import PlayerProfile
        c,i,race=fixture();call_command('seed_khorinis',stdout=StringIO())
        p=person(c,'OLD_CAMP','BARON');p.level=45;p.mana=300;p.current_mana=0;p.mana_updated_at=timezone.now();p.ore_balance=10000;p.save();succeed(race)
        bp=ItemBluePrint.objects.get(catalog_key='g2nk-itpo_mana_03');self.assertTrue(game.buy_item_from_npc(p,bp));item=p.inventory.get(blueprint=bp);gate=Barrier(2);now=timezone.now()
        def worker(_):
            connections.close_all()
            try:
                actor=PlayerProfile.objects.get(pk=p.pk);owned=OwnedItem.objects.get(pk=item.pk);gate.wait(timeout=10);return game.use_item(actor,owned)
            finally:connections.close_all()
        with patch('django.utils.timezone.now',return_value=now),ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(worker,range(2)))
        self.assertEqual(sorted(results),[False,True]);p.refresh_from_db();self.assertEqual(p.current_mana,100);self.assertFalse(p.inventory.filter(pk=item.pk).exists())
