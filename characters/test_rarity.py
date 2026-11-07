import hashlib, io, json, os, sqlite3, subprocess, sys, tempfile
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase, SimpleTestCase
from .models import ItemBluePrint, OwnedItem, LootTable, BattleRecord
from .equipment import add_item
from .enhancements import improve_item, QUALITY_RANKS
from .gear_loot import roll_rarity, award_gear, RARITY_WEIGHTS, BOSS_RARITY_WEIGHTS
from . import game_logic as game


class RarityTests(TestCase):
    def setUp(self):
        call_command('seed_equipment', stdout=io.StringIO())
        self.p=User.objects.create_user('rarity-player').playerprofile
        self.p.ore_balance=10000;self.p.save()
        self.bp=ItemBluePrint.objects.create(name='Miecz próby',damage=20,base_value=100)
        self.dust=add_item(self.p,ItemBluePrint.objects.get(catalog_key='rune-dust'),200)
        self.client.force_login(self.p.user)

    def test_five_names_and_independent_three_step_forge_all_rarities(self):
        self.assertEqual([r['name'] for r in QUALITY_RANKS],['Niewykończony','Mistrzowski','Nasycony magią','Runiczny','Pradawny'])
        for rank in range(5):
            item=add_item(self.p,self.bp,origin='loot',rarity=rank)
            for level in range(3):
                self.assertTrue(improve_item(self.p,item.pk,level,uuid4()))
                item.refresh_from_db();self.assertEqual(item.rarity,rank)
                self.assertEqual(item.upgrade_level,level+1)
            before=self.p.ore_balance
            self.assertFalse(improve_item(self.p,item.pk,3,uuid4()))
            self.assertEqual(self.p.ore_balance,before)
            self.assertIn('+3',item.display_name)
            self.assertIsNone(item.upgrade_cost)

    def test_rarity_cannot_be_changed_by_save_or_forged_post(self):
        item=add_item(self.p,self.bp,rarity=1)
        item.rarity=4
        with self.assertRaises(ValidationError):item.save()
        item.refresh_from_db()
        self.client.post('/ekwipunek/',{'action':'improve','item_id':item.pk,'expected_level':0,'request_key':uuid4(),'rarity':4,'level':3,'ore':0})
        item.refresh_from_db();self.assertEqual((item.rarity,item.upgrade_level),(1,1))
        with self.assertRaises(IntegrityError), transaction.atomic():
            OwnedItem.objects.filter(pk=item.pk).update(upgrade_level=4)
        with self.assertRaises(IntegrityError), transaction.atomic():
            OwnedItem.objects.filter(pk=item.pk).update(rarity=5)

    def test_same_request_never_rerolls_rarity_or_double_spends(self):
        item=add_item(self.p,self.bp,rarity=3)
        key=uuid4();first=improve_item(self.p,item.pk,0,key)
        self.p.refresh_from_db();before=self.p.ore_balance
        for _ in range(5):self.assertEqual(improve_item(self.p,item.pk,0,key).pk,first.pk)
        item.refresh_from_db();self.assertEqual((item.rarity,item.upgrade_level),(3,1))
        self.assertEqual(self.p.ore_balance,before)
        self.assertFalse(improve_item(self.p,item.pk,0,uuid4()))
        self.assertEqual(first.snapshot['rarity'],3)

    def test_loot_snapshot_replay_trade_and_rarity_filter(self):
        self.p.strength=100;self.p.save()
        LootTable.objects.update_or_create(key='young_scavenger',defaults={'entries':[{'blueprint':self.bp.pk,'weight':10000}]})
        with patch('characters.gear_loot.roll_rarity',return_value=4),patch('characters.gear_loot.award_gear',return_value=[]):
            key=uuid4();self.assertTrue(game.execute_hunt(self.p,'young_scavenger','exchange',key))
            self.assertTrue(game.execute_hunt(self.p,'young_scavenger','exchange',key))
        item=self.p.inventory.get(blueprint=self.bp)
        self.assertEqual((item.rarity,item.upgrade_level),(4,0))
        record=BattleRecord.objects.get(profile=self.p)
        self.assertEqual((record.loot[0]['rarity_key'],record.loot[0]['quantity']),('ancient',1))
        self.assertContains(self.client.get('/ekwipunek/',{'quality':'ancient'}),'Pradawny')
        self.assertTrue(game.list_item_on_market(self.p,item,20))
        other=User.objects.create_user('rarity-buyer').playerprofile
        self.assertTrue(game.buy_item_on_market(other,item))
        self.assertTrue(improve_item(other,item.pk,0,uuid4()) is False) # no earned dust
        item.refresh_from_db();self.assertEqual((item.rarity,item.upgrade_level),(4,0))
        self.assertEqual(BattleRecord.objects.get().loot,record.loot)

    def test_regular_and_boss_gear_have_rarity_and_no_forge_level(self):
        for boss in [False,True]:
            with patch('characters.gear_loot.roll_rarity',return_value=3):
                drops=award_gear(self.p,0,boss=boss,guaranteed=True)
            self.assertEqual((drops[0]['rarity'],drops[0]['upgrade_level']),(3,0))
            self.assertEqual(OwnedItem.objects.get(pk=drops[0]['item_id']).rarity,3)

    def test_npc_craft_and_stacks_do_not_generate_legendary_items(self):
        self.assertTrue(game.buy_item_from_npc(self.p,self.bp))
        self.assertEqual(self.p.inventory.get(blueprint=self.bp).rarity,0)
        with self.assertRaises(ValueError):add_item(self.p,self.dust.blueprint,rarity=4)
        with self.assertRaises(ValueError):add_item(self.p,self.bp,quantity=2,rarity=4)

    def test_no_health_or_mana_from_rarity_or_forge(self):
        bp=ItemBluePrint.objects.create(name='Amulet próby',kind='amulet',life_bonus=20,mana_bonus=10)
        item=add_item(self.p,bp,rarity=4)
        self.p.current_health=20;self.p.current_mana=3;self.p.save()
        self.assertTrue(game.equip_item(self.p,item))
        self.assertTrue(improve_item(self.p,item.pk,0,uuid4()))
        self.p.refresh_from_db();self.assertEqual((self.p.current_health,self.p.current_mana),(20,3))


class RarityRulesTests(SimpleTestCase):
    def test_every_boundary_and_exact_normal_boss_weights(self):
        for boss,weights in [(False,RARITY_WEIGHTS),(True,BOSS_RARITY_WEIGHTS)]:
            self.assertEqual(sum(weights),10000)
            start=0
            for rank,weight in enumerate(weights):
                for roll in [start,start+weight-1]:
                    with patch('characters.gear_loot.random.randrange',return_value=roll):self.assertEqual(roll_rarity(boss=boss),rank)
                start+=weight
        self.assertEqual(RARITY_WEIGHTS,(6000,2500,1000,400,100))
        self.assertEqual(BOSS_RARITY_WEIGHTS,(4000,3000,1800,1000,200))

    def test_pg_legacy_proof_preserves_power_but_current_proof_distinguishes_fields(self):
        from .management.commands.import_sqlite_world import canonical
        old=[{'model':'characters.owneditem','pk':1,'fields':{'upgrade_level':10,'quantity':1}}]
        new=[{'model':'characters.owneditem','pk':1,'fields':{'rarity':4,'upgrade_level':2,'quantity':1}}]
        self.assertEqual(canonical(json.dumps(old)),canonical(json.dumps(new),legacy_equipment=True))
        different=[{'model':'characters.owneditem','pk':1,'fields':{'rarity':3,'upgrade_level':3,'quantity':1}}]
        self.assertNotEqual(canonical(json.dumps(new)),canonical(json.dumps(different)))
        new[0]['fields']['quantity']=2
        self.assertNotEqual(canonical(json.dumps(old)),canonical(json.dumps(new),legacy_equipment=True))

    def test_old_sqlite_backup_all_power_steps_preserve_items_balances_and_hashes(self):
        from ore_empire.database import sqlite_environment
        from .backups import create_backup,restore_drill,inspect_database
        with tempfile.TemporaryDirectory(prefix='ore-rarity-migration-') as tmp:
            root=Path(tmp);source=root/'old.sqlite3';target=root/'restored.sqlite3';env=sqlite_environment(source)
            result=subprocess.run([sys.executable,'manage.py','migrate','characters','0036','--noinput'],cwd=settings.BASE_DIR,env=env,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr.decode())
            script="""import os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','ore_empire.settings');import django;django.setup()
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
apps=MigrationExecutor(connection).loader.project_state([('characters','0036_ochrona_rynsztunku')]).apps
U=apps.get_model('auth','User');P=apps.get_model('characters','PlayerProfile');B=apps.get_model('characters','ItemBluePrint');I=apps.get_model('characters','OwnedItem');W=apps.get_model('characters','World')
u=U.objects.create(username='synthetic',password='private-test-hash');p=P.objects.create(user=u,world=W.objects.first(),ore_balance=5432);bp=B.objects.create(name='Old blade',damage=20,life_bonus=10)
for level in range(11):I.objects.create(owner=p,blueprint=bp,upgrade_level=level,is_protected=bool(level%2))
"""
            result=subprocess.run([sys.executable,'-c',script],cwd=settings.BASE_DIR,env=env,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr.decode())
            before=inspect_database(source);backup=create_backup(source,root/'backups');restore_drill(backup,target,source)
            self.assertEqual(inspect_database(target,{k:v['columns'] for k,v in before.items()}),before)
            with sqlite3.connect(target) as db:
                rows=db.execute('SELECT rarity,upgrade_level FROM characters_owneditem ORDER BY id').fetchall()
            self.assertEqual([2*r+u for r,u in rows],list(range(11)))
            self.assertEqual(rows[-1],(4,2))
            current=inspect_database(target)
            self.assertIn('rarity',current['characters_owneditem']['columns'])
            with sqlite3.connect(target) as db:db.execute('UPDATE characters_owneditem SET rarity=3,upgrade_level=3 WHERE rarity=4 AND upgrade_level=2')
            self.assertNotEqual(inspect_database(target),current)


class RareBotEquipmentTests(TestCase):
    def setUp(self):
        self.p=User.objects.create_user('rare-bot').playerprofile
        self.p.is_bot=True;self.p.camp='OLD_CAMP';self.p.guild='BARON';self.p.ore_balance=100;self.p.bot_turn=3;self.p.save()
        self.bp=ItemBluePrint.objects.create(name='Broń podstawowa',damage=20,base_value=100,merchant=False)
        self.worn=add_item(self.p,self.bp);game.equip_item(self.p,self.worn)

    def test_bot_buys_weaker_base_but_stronger_rare_offer_and_respects_dexterity(self):
        from .bots import tick_bot
        seller=User.objects.create_user('rare-seller').playerprofile
        bp=ItemBluePrint.objects.create(name='Rzadki miecz',damage=18,base_value=100,merchant=False)
        offer=add_item(seller,bp,origin='loot',rarity=4);game.list_item_on_market(seller,offer,60)
        forbidden_bp=ItemBluePrint.objects.create(name='Za trudny miecz',damage=100,base_value=100,merchant=False,required_dexterity=99)
        forbidden=add_item(seller,forbidden_bp);game.list_item_on_market(seller,forbidden,1)
        self.assertEqual(tick_bot(self.p),('buy',True))
        offer.refresh_from_db();self.assertEqual((offer.owner_id,offer.rarity),(self.p.pk,4))
        self.assertEqual(tick_bot(self.p),('equip',True))
        self.assertEqual(tick_bot(self.p),('sell',True))
        offer.refresh_from_db();self.assertTrue(offer.is_equipped)
        forbidden.refresh_from_db();self.assertEqual(forbidden.owner_id,seller.pk)

    def test_stronger_rare_spare_is_equipped_instead_of_sold_by_base_damage(self):
        from .bots import tick_bot
        bp=ItemBluePrint.objects.create(name='Rzadki łup',damage=18,base_value=100,merchant=False)
        item=add_item(self.p,bp,rarity=4,origin='loot')
        self.assertEqual(tick_bot(self.p),('equip',True))
        item.refresh_from_db();self.assertTrue(item.is_equipped)
        self.worn.refresh_from_db();self.assertFalse(self.worn.is_equipped)

    def test_protected_spare_does_not_become_a_sale_plan(self):
        from .bots import tick_bot
        from .models import BotDecision
        bp=ItemBluePrint.objects.create(name='Pamiątka',damage=1,base_value=100,merchant=False)
        item=add_item(self.p,bp);item.is_protected=True;item.save()
        from .models import MarketEvent
        MarketEvent.objects.create(profile=self.p,item=item,blueprint=bp,action='cancellation',reason='stale',price=100)
        tick_bot(self.p)
        observation=BotDecision.objects.filter(profile=self.p).first().observation
        self.assertNotEqual(observation['disposal_id'],item.pk)
        self.assertNotEqual(observation['inventory_id'],item.pk)
        self.assertNotEqual(observation['market_action'],'market_sell')
        item.refresh_from_db();self.assertFalse(item.is_market_listed)
