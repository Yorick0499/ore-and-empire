from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from .models import OwnedItem,ItemBluePrint,MarketTrade,MarketEvent
from .market_policy import bot_market_plan,reprice_listing,reference_price,market_effectiveness
from .game_logic import list_item_on_market,delist_item_from_market,buy_item_on_market
from .management.commands.simulate_market import scenario

class MarketPolicyTests(TestCase):
    def setUp(self):
        self.seller=User.objects.create_user('seller').playerprofile;self.seller.is_bot=True;self.seller.bot_role='trader';self.seller.save()
        self.buyer=User.objects.create_user('buyer').playerprofile;self.buyer.ore_balance=500;self.buyer.save()
        self.bp=ItemBluePrint.objects.create(name='Towar',base_value=100)
        self.item=OwnedItem.objects.create(owner=self.seller,blueprint=self.bp)
    def test_listing_repricing_cancellation_history_and_stale_price(self):
        self.assertTrue(list_item_on_market(self.seller,self.item,110))
        self.item.listed_at=timezone.now()-timedelta(days=2);self.item.save()
        action,target,price=bot_market_plan(self.seller);self.assertEqual((action,target),('market_reprice',self.item.pk))
        self.assertTrue(reprice_listing(self.seller,self.item,price,110));self.assertFalse(reprice_listing(self.seller,self.item,70,110))
        self.item.listed_at=timezone.now()-timedelta(days=4);self.item.save()
        self.assertEqual(bot_market_plan(self.seller)[0],'market_cancel')
        self.assertTrue(delist_item_from_market(self.seller,self.item,'stale'))
        self.assertEqual(bot_market_plan(self.seller)[0],'market_sell')
        self.assertEqual(set(MarketEvent.objects.values_list('action',flat=True)),{'listing','repricing','cancellation'})
    def test_unit_price_uses_real_trades_and_is_bounded(self):
        MarketTrade.objects.create(blueprint=self.bp,seller=self.seller,buyer=self.buyer,price=500,quantity=10)
        self.assertEqual(reference_price(self.bp,self.seller.world_id),60)
        MarketTrade.objects.all().delete()
        MarketTrade.objects.create(blueprint=self.bp,seller=self.seller,buyer=self.buyer,price=9999,quantity=1)
        self.assertEqual(reference_price(self.bp,self.seller.world_id),140)
    def test_bot_buys_only_needed_healing_and_budget_is_real(self):
        self.bp.kind='consumable';self.bp.heal_amount=40;self.bp.base_value=25;self.bp.save()
        list_item_on_market(self.seller,self.item,25)
        self.buyer.current_health=15;self.buyer.save()
        action,target,_=bot_market_plan(self.buyer);self.assertEqual((action,target),('market_buy',self.item.pk))
        self.assertTrue(buy_item_on_market(self.buyer,self.item));self.buyer.refresh_from_db();self.assertEqual(self.buyer.ore_balance,475)
        self.assertEqual(MarketTrade.objects.get().quantity,1)
        self.assertEqual(bot_market_plan(self.buyer)[0],'')
    def test_event_write_failure_rolls_back_listing_and_multi_day_model_frees_stock(self):
        with patch.object(MarketEvent.objects,'create',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):list_item_on_market(self.seller,self.item,100)
        self.item.refresh_from_db();self.assertFalse(self.item.is_market_listed)
        self.assertEqual(scenario(False,False)['remaining_items'],1)
        self.assertEqual(scenario(True,False)['remaining_items'],0)
        self.assertIsNotNone(scenario(True,True)['real_demand_sale_day'])
        self.assertEqual(scenario(True,True)['policy_currency_grants'],0)

    def test_unknown_legacy_age_stays_unknown_but_observed_stock_can_be_cancelled(self):
        from .market_policy import observe_legacy_listing
        self.item.is_market_listed=True;self.item.market_price=110;self.item.save()
        self.assertEqual(bot_market_plan(self.seller)[0],'market_observe')
        self.assertTrue(observe_legacy_listing(self.seller,self.item));self.item.refresh_from_db();self.assertIsNone(self.item.listed_at)
        with patch('django.utils.timezone.now',return_value=timezone.now()+timedelta(days=4)):
            self.assertEqual(bot_market_plan(self.seller)[0],'market_cancel')
