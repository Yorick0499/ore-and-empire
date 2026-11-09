from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from .models import OwnedItem,ItemBluePrint,MarketTrade
from .equipment import add_item
from . import game_logic as game
from .market_intelligence import MarketState,retention,sale_candidate,score
from .market_policy import list_bot_surplus,bot_market_plan
from .weapon_finance import finance,plan

class IntelligentMarketTests(TestCase):
    def setUp(self):
        self.s=User.objects.create_user('sprzedawca').playerprofile;self.s.is_bot=True;self.s.ore_balance=500;self.s.save()
        self.b=User.objects.create_user('nabywca').playerprofile;self.b.ore_balance=500;self.b.save()
        self.bp=ItemBluePrint.objects.create(name='Przydatny miecz',damage=20,base_value=100,merchant=False,required_strength=10)
        self.item=add_item(self.s,self.bp)
        self.best=add_item(self.s,ItemBluePrint.objects.create(name='Własny miecz',damage=40,base_value=200,merchant=False))
        game.equip_item(self.s,self.best)
    def test_junk_and_no_eligible_buyer_do_not_create_artificial_demand(self):
        junk=add_item(self.s,ItemBluePrint.objects.create(name='Drewniany kij',damage=1,base_value=5))
        self.assertEqual(MarketState(self.s.world_id).quote(self.s,junk).price,0)
        self.b.strength=1;self.b.save()
        self.assertEqual(MarketState(self.s.world_id).quote(self.s,self.item).price,0)
    def test_supply_reduces_price_and_limits_listing(self):
        initial=MarketState(self.s.world_id).quote(self.s,self.item).price
        for n in range(5):
            other=User.objects.create_user('zapas-'+str(n)).playerprofile
            OwnedItem.objects.create(owner=other,blueprint=self.bp,is_market_listed=True,market_price=100)
        state=MarketState(self.s.world_id)
        self.assertLess(state.quote(self.s,self.item).price,initial)
        self.assertIsNone(sale_candidate(self.s,list(self.s.inventory.select_related('blueprint')),market=state))
    def test_equivalent_npc_substitute_caps_price(self):
        ItemBluePrint.objects.create(name='Zamiennik',damage=21,base_value=70)
        q=MarketState(self.s.world_id).quote(self.s,self.item)
        self.assertLessEqual(q.price,round(70*.95));self.assertGreater(q.price,50)
    def test_best_future_and_protected_gear_are_retained(self):
        future=add_item(self.s,ItemBluePrint.objects.create(name='Na później',damage=60,required_strength=20,merchant=False))
        keep=retention(self.s,list(self.s.inventory.select_related('blueprint')))
        self.assertTrue({future.pk,self.best.pk}<=keep)
        self.assertFalse(list_bot_surplus(self.s,self.best))
        self.assertTrue(list_bot_surplus(self.s,self.item))
        duplicate=add_item(self.s,self.bp);self.assertFalse(list_bot_surplus(self.s,duplicate))
    def test_legacy_best_listing_is_rescued(self):
        game.unequip_item(self.s,self.best);game.list_item_on_market(self.s,self.best,200)
        self.assertEqual(bot_market_plan(self.s)[:2],('market_cancel',self.best.pk))
    def test_variant_snapshots_and_repeated_buyer_do_not_poison_history(self):
        rare=add_item(self.s,self.bp,rarity=4)
        price=MarketState(self.s.world_id).quote(self.s,rare).price
        MarketTrade.objects.create(seller=self.s,buyer=self.b,blueprint=self.bp,price=99999,quantity=1)
        self.assertEqual(MarketState(self.s.world_id).quote(self.s,rare).price,price)
        for _ in range(25):MarketTrade.objects.create(seller=self.s,buyer=self.b,blueprint=self.bp,price=130,quantity=1,rarity=0,upgrade_level=0)
        self.assertEqual(MarketState(self.s.world_id).quote(self.s,self.item).sales,1)
        game.list_item_on_market(self.s,rare,150);self.assertTrue(game.buy_item_on_market(self.b,rare,150))
        t=MarketTrade.objects.first();self.assertEqual((t.rarity,t.upgrade_level),(4,0))
    def test_build_score_does_not_switch_strength_warrior_to_bad_bow(self):
        self.s.strength=100;self.s.dexterity=10
        bow=ItemBluePrint.objects.create(name='Łuk',damage=50,weapon_type='bow')
        self.assertLess(score(self.s,bow),score(self.s,self.best))
    def test_financing_replacement_is_atomic_and_preserves_rare_gear(self):
        self.s.ore_balance=30;self.s.save()
        better=ItemBluePrint.objects.create(name='Dostępny zamiennik',damage=80,base_value=100)
        self.assertEqual(plan(self.s,list(self.s.inventory.select_related('blueprint')),[better]),better)
        with patch('characters.game_logic.buy_item_from_npc',return_value=False):
            self.assertFalse(finance(self.s,self.best.pk,better.pk,100))
        self.best.refresh_from_db();self.s.refresh_from_db()
        self.assertTrue(self.best.is_equipped);self.assertEqual(self.s.ore_balance,30)
        self.assertFalse(finance(self.s,self.best.pk,better.pk,101))
        self.assertTrue(finance(self.s,self.best.pk,better.pk,100))
        self.assertEqual(self.s.inventory.get(is_equipped=True).blueprint_id,better.pk)
