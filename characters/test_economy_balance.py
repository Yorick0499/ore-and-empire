from datetime import timedelta
from io import StringIO
from uuid import uuid4
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase,SimpleTestCase
from django.utils import timezone
from .models import EconomicEntry,EnergyRefill,ItemBluePrint,OwnedItem,StoreProduct
from .economic_ledger import summary,refills_remaining
from .economy import purchase_product
from .admin_tools import administer_player
from . import game_logic as game
from .economy_simulation import simulation_report,actor_budget


class EconomyLedgerTests(TestCase):
    def setUp(self):
        self.seller=User.objects.create_user('seller').playerprofile
        self.buyer=User.objects.create_user('buyer').playerprofile
        self.weapon=ItemBluePrint.objects.create(name='Blade',damage=10,base_value=20)

    def test_opening_transfer_source_and_sink_reconcile_without_minting_turnover(self):
        self.assertEqual(EconomicEntry.objects.filter(category='opening').count(),2)
        game.buy_item_from_npc(self.seller,self.weapon)
        item=self.seller.inventory.get()
        game.list_item_on_market(self.seller,item,15)
        self.assertTrue(game.buy_item_on_market(self.buyer,item))
        data=summary()
        self.assertEqual(data['resources']['ore']['source'],0)
        self.assertEqual(data['resources']['ore']['sink'],-20)
        self.assertEqual(data['resources']['ore']['transfer'],0)
        self.assertEqual(data['market_turnover'],15)
        self.assertEqual(data['resources']['ore']['actual_balance'],80)
        self.assertEqual(data['resources']['ore']['reconciliation_gap'],0)
        transfer=list(EconomicEntry.objects.filter(category='transfer'))
        self.assertEqual(len(transfer),2)
        self.assertEqual(transfer[0].reference,transfer[1].reference)
        self.assertEqual(sum(e.amount for e in transfer),0)
        game.sell_item_from_npc(self.buyer,item)
        self.assertEqual(summary()['resources']['ore']['source'],10)

    def test_ledger_error_rolls_back_purchase_and_inventory(self):
        with patch('characters.economic_ledger.EconomicEntry.objects.create',side_effect=RuntimeError('unavailable')):
            with self.assertRaises(RuntimeError):game.buy_item_from_npc(self.buyer,self.weapon)
        self.buyer.refresh_from_db()
        self.assertEqual(self.buyer.ore_balance,50)
        self.assertFalse(self.buyer.inventory.exists())

    def test_admin_credit_is_separate_from_game_rewards(self):
        admin=User.objects.create_superuser('gm',password='test-only')
        success,_=administer_player(admin,self.buyer.pk,'premium',{'amount':10})
        self.assertTrue(success)
        data=summary()
        self.assertEqual(data['resources']['shards']['admin'],10)
        self.assertEqual(data['resources']['shards']['source'],0)
        self.assertEqual(data['resources']['shards']['reconciliation_gap'],0)

    def test_refill_limit_is_shared_replay_safe_and_resets_at_utc_midnight(self):
        admin=User.objects.create_superuser('gm',password='test-only')
        administer_player(admin,self.buyer.pk,'premium',{'amount':30})
        self.buyer.refresh_from_db()
        product=StoreProduct.objects.create(key='energy',name='Drink',kind='energy',price=3,effect=25)
        potion=ItemBluePrint.objects.create(name='Backpack energy',kind='consumable',energy_amount=25,stackable=True)
        stack=OwnedItem.objects.create(owner=self.buyer,blueprint=potion,quantity=3)
        keys=[]
        now=timezone.now().replace(hour=12)
        with patch('django.utils.timezone.now',return_value=now):
            for _ in range(3):
                self.buyer.current_energy=0;self.buyer.save()
                key=uuid4();keys.append(key)
                self.assertTrue(purchase_product(self.buyer,product.pk,key))
            for _ in range(2):
                self.buyer.current_energy=0;self.buyer.save()
                self.assertTrue(game.use_item(self.buyer,stack))
                stack.refresh_from_db()
            self.assertEqual(refills_remaining(self.buyer),0)
            self.buyer.current_energy=0;self.buyer.save()
            self.assertFalse(game.use_item(self.buyer,stack))
            self.assertFalse(purchase_product(self.buyer,product.pk,uuid4()))
            self.assertTrue(purchase_product(self.buyer,product.pk,keys[0]))
            self.assertEqual(EnergyRefill.objects.count(),5)
        with patch('django.utils.timezone.now',return_value=now+timedelta(days=1)):
            self.assertEqual(refills_remaining(self.buyer),5)

    def test_admin_report_is_not_public(self):
        self.client.force_login(self.buyer.user)
        self.assertEqual(self.client.get('/zarzadca/gospodarka/').status_code,302)
        admin=User.objects.create_superuser('gm',password='test-only')
        self.client.force_login(admin)
        self.assertContains(self.client.get('/zarzadca/gospodarka/'),'Bilans gospodarki')


class EconomyModelTests(SimpleTestCase):
    def test_stress_matrix_and_refill_counterfactual_are_reproducible(self):
        report=simulation_report()
        self.assertEqual(len(report['cases']),18)
        self.assertEqual({c['days'] for c in report['cases']},{10,30,90})
        self.assertEqual({c['population'] for c in report['cases']},{6,20,50})
        for case in report['cases']:
            self.assertGreaterEqual(case['totals']['ore'],0)
            self.assertGreaterEqual(case['totals']['shards'],0)
            self.assertLessEqual(case['totals']['refills'],case['days']*5*case['population'])
        comparison=report['courier_event_refill_comparison_90d']
        self.assertGreater(comparison['uncapped']['adventures'],comparison['capped']['adventures'])
        self.assertLessEqual(comparison['capped']['refills'],450)
        self.assertEqual(report,simulation_report())
