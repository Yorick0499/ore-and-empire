"""Actionable read-only resource forecasts and isolated build rehearsal contract."""
import json,tempfile
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command,CommandError
from django.test import TestCase,SimpleTestCase
from .models import ItemBluePrint,OwnedItem
from .magic import prepare_magic
from .combat_preparation import hunt_preparation

class BuildForecastTests(TestCase):
    def setUp(self):
        self.p=User.objects.create_user('forecast-build').playerprofile
        self.p.camp='OLD_CAMP';self.p.guild='FIRE_MAGE';self.p.level=15;self.p.magic_skill=1;self.p.mana=40;self.p.current_mana=8;self.p.save()
        bp=ItemBluePrint.objects.create(name='Runa pocisku',catalog_key='g1-itarrunefirebolt',kind='rune')
        item=OwnedItem.objects.create(owner=self.p,blueprint=bp);self.assertTrue(prepare_magic(self.p,item.pk))
    def test_mana_and_resistance_forecast_never_spends_or_rolls(self):
        before=type(self.p).objects.values().get(pk=self.p.pk)
        target={'life':100,'strength':8,'weapon_prot':2,'fire_prot':4}
        with patch('characters.game_logic.random.randint',side_effect=RuntimeError('no rolls')):row=hunt_preparation(self.p,{'target':target})['forecasts']['target']['magic']
        self.assertEqual(row,{'damage':20,'casts':5,'available':2,'mana':20,'short':True})
        self.assertEqual(type(self.p).objects.values().get(pk=self.p.pk),before)
    def test_scroll_quantity_limits_the_forecast(self):
        bp=ItemBluePrint.objects.create(name='Zwój',catalog_key='g1-itarscrollfirebolt',kind='scroll',stackable=True)
        item=OwnedItem.objects.create(owner=self.p,blueprint=bp,quantity=1);self.assertTrue(prepare_magic(self.p,item.pk))
        row=hunt_preparation(self.p,{'target':{'life':100,'strength':8,'weapon_prot':0}})['forecasts']['target']['magic']
        self.assertEqual((row['available'],row['mana']),(1,5));item.refresh_from_db();self.assertEqual(item.quantity,1)
    def test_boss_uses_own_energy_cost_and_shows_resources(self):
        self.client.force_login(self.p.user);self.p.current_energy=20;self.p.current_mana=0;self.p.save()
        response=self.client.get('/wyprawa/?location=crawler_nest')
        self.assertContains(response,'Przygotowanie do wyprawy');self.assertContains(response,'ta walka kosztuje 25')
        self.assertContains(response,'potem walczysz pięściami');self.assertNotContains(response,'<button>Rozpocznij wyprawę',html=False)
    def test_training_explains_builds_reserves_and_funding(self):
        self.client.force_login(self.p.user);response=self.client.get('/trening/')
        for phrase in ('Jak rozwijać swój build?','Łucznik','Zachowaj PN','Sprawdź wymagania awansu'):self.assertContains(response,phrase)

class BuildRehearsalCommandTests(SimpleTestCase):
    def test_selected_cases_are_isolated_and_missing_facts_cannot_pass(self):
        with tempfile.TemporaryDirectory() as root:
            target=Path(root)/'report.json'
            with patch('characters.management.commands.simulate_builds.subprocess.run',return_value=SimpleNamespace(returncode=0)) as child:
                with self.assertRaises(CommandError):call_command('simulate_builds',report=target,cases=['new-archer'],stdout=StringIO())
            env=child.call_args.kwargs['env'];self.assertEqual(env['DATABASE_URL'],'');self.assertEqual(env['ORE_DATABASE_ENGINE'],'sqlite')
            self.assertIn('test_new_archer',str(child.call_args.args[0]));self.assertFalse(Path(env['ORE_DATABASE_PATH']).parent.exists());self.assertFalse(json.loads(target.read_text())['success'])
            before=target.read_bytes()
            with self.assertRaises(CommandError):call_command('simulate_builds',report=target,cases=['new-archer'],stdout=StringIO())
            self.assertEqual(target.read_bytes(),before)

class ScrollSupplyTests(TestCase):
    def setUp(self):
        from .magic import prepare_magic
        self.p=User.objects.create_user('scroll-supply').playerprofile
        self.p.current_mana=10;self.p.mana=10;self.p.life=500;self.p.current_health=500;self.p.save()
        self.bp=ItemBluePrint.objects.create(name='Osobny zwój G1',kind='scroll',catalog_key='g1-itarscrollfirebolt',stackable=False)
        self.one=OwnedItem.objects.create(owner=self.p,blueprint=self.bp)
        self.two=OwnedItem.objects.create(owner=self.p,blueprint=self.bp)
        self.assertTrue(prepare_magic(self.p,self.one.pk))
    def test_two_nonstackable_scrolls_are_cast_without_free_ammunition_or_replay(self):
        from uuid import uuid4
        from . import game_logic as game
        from .magic import combat_plan
        self.assertEqual(combat_plan(self.p).quantity,2);key=uuid4()
        self.assertTrue(game.execute_hunt(self.p,'scavenger','forest',key))
        self.p.refresh_from_db();row=self.p.battles.first()
        self.assertEqual(row.combat_details['casts'],2);self.assertEqual(self.p.current_mana,8)
        self.assertFalse(self.p.inventory.filter(blueprint=self.bp).exists());self.assertIsNone(self.p.prepared_magic_id)
        self.assertTrue(game.execute_hunt(self.p,'scavenger','forest',key));self.p.refresh_from_db()
        self.assertEqual(self.p.current_mana,8);self.assertEqual(self.p.battles.count(),1)
    def test_magic_page_shows_the_combined_supply_without_spending(self):
        self.client.force_login(self.p.user)
        self.assertContains(self.client.get('/magia/'),'dostępnych sztuk do walki: 2')
        self.assertEqual(self.p.inventory.filter(blueprint=self.bp).count(),2)
    def test_remaining_scroll_becomes_prepared_after_first_item_was_consumed(self):
        from . import game_logic as game
        self.assertTrue(game.execute_hunt(self.p,'young_scavenger','forest'))
        self.p.refresh_from_db();self.assertEqual(self.p.prepared_magic_id,self.two.pk)
        self.assertFalse(OwnedItem.objects.filter(pk=self.one.pk).exists());self.two.refresh_from_db();self.assertEqual(self.two.quantity,1)
    def test_protected_or_listed_additional_items_are_never_consumed(self):
        from .magic import combat_plan
        from . import game_logic as game
        self.two.is_protected=True;self.two.save()
        listed=OwnedItem.objects.create(owner=self.p,blueprint=self.bp,is_market_listed=True,market_price=10)
        # Explicitly prepared protected item remains an intentional consumable.
        self.one.is_protected=True;self.one.save()
        self.assertEqual(combat_plan(self.p).quantity,1)
        self.assertTrue(game.execute_hunt(self.p,'young_scavenger','forest'))
        self.two.refresh_from_db();listed.refresh_from_db()
        self.assertEqual((self.two.quantity,listed.quantity),(1,1));self.assertTrue(listed.is_market_listed)
    def test_missing_supply_fails_before_partial_deletion(self):
        from types import SimpleNamespace
        from .magic import combat_plan,apply_combat_magic
        plan=combat_plan(self.p)
        with self.assertRaises(ValueError):apply_combat_magic(self.p,plan,SimpleNamespace(remaining_mana=7,spell_casts=3))
        self.assertEqual(list(self.p.inventory.filter(blueprint=self.bp).order_by('pk').values_list('quantity',flat=True)),[1,1])

from django.test import TransactionTestCase,skipUnlessDBFeature
class ScrollSupplyContentionTests(TransactionTestCase):
    setUp=ScrollSupplyTests.setUp
    @skipUnlessDBFeature('has_select_for_update')
    def test_same_request_from_two_connections_consumes_the_pool_once(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from uuid import uuid4
        from django.db import connections
        from .models import PlayerProfile
        from . import game_logic as game
        gate=Barrier(2);key=uuid4();pk=self.p.pk
        def worker(_):
            connections.close_all()
            try:
                actor=PlayerProfile.objects.get(pk=pk);gate.wait(timeout=10)
                return bool(game.execute_hunt(actor,'scavenger','forest',key))
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:self.assertEqual(list(pool.map(worker,range(2))),[True,True])
        self.p.refresh_from_db();self.assertEqual(self.p.current_mana,8);self.assertEqual(self.p.battles.count(),1)
        self.assertFalse(self.p.inventory.filter(blueprint=self.bp).exists())
