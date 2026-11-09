"""Real independent PostgreSQL connections; never emulate row locks with SQLite."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO
from threading import Barrier,Event
from unittest import skipUnless
from uuid import uuid4
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection,connections
from django.test import TransactionTestCase,TestCase,SimpleTestCase
from django.utils import timezone
from .models import ItemBluePrint,OwnedItem,MarketTrade,PlayerProfile,AdventureTemplate,AdventureRun,StoreProduct,StorePurchase,CampQuest,SchedulerLease
from . import game_logic as game
from .scheduler_lease import SchedulerGuard,LeaseLost

class DatabaseConfigTests(SimpleTestCase):
    def test_sqlite_isolated_environment_cannot_inherit_postgresql(self):
        from unittest.mock import patch
        from ore_empire.database import database_config,sqlite_environment
        from pathlib import Path
        with patch.dict('os.environ',{'DATABASE_URL':'postgresql://private:secret@db/world','ORE_DATABASE_ENGINE':'postgresql'}):env=sqlite_environment('/tmp/separate.sqlite3')
        self.assertNotIn('DATABASE_URL',env)
        self.assertEqual(database_config(env,Path('/tmp'))['NAME'],'/tmp/separate.sqlite3')
    def test_save_serializer_keeps_microseconds_and_zero_fraction(self):
        import json
        from datetime import datetime,timezone
        from ore_empire.precise_json import PreciseEncoder
        self.assertIn('.123456Z',json.dumps(datetime(2026,1,1,microsecond=123456,tzinfo=timezone.utc),cls=PreciseEncoder))
        self.assertIn('.000000Z',json.dumps(datetime(2026,1,1,tzinfo=timezone.utc),cls=PreciseEncoder))
    def test_training_is_not_starved_by_optional_patrol_and_replay_remains_frozen(self):
        from .bots import Observation,BaselinePolicy,BaselinePolicyV17
        o=Observation(100,100,False,False,None,None,None,None,True,training_needed=True,skill_points=10,patrol_depth=1)
        self.assertEqual(BaselinePolicy().choose(o),('train',None))
        self.assertEqual(BaselinePolicyV17().choose(o),('patrol',1))
    def test_postgresql_configuration_and_invalid_backend(self):
        from ore_empire.database import database_config
        from django.core.exceptions import ImproperlyConfigured
        from pathlib import Path
        config=database_config({'DATABASE_URL':'postgresql://resident:p%40ss@localhost:5434/colony?sslmode=require'},Path('/tmp'))
        self.assertEqual((config['NAME'],config['PASSWORD'],config['PORT']),('colony','p@ss',5434))
        with self.assertRaises(ImproperlyConfigured):database_config({'DATABASE_URL':'https://db/private'},Path('/tmp'))

class LeaseTests(TestCase):
    def setUp(self):
        from .worlds import current_world
        self.world=current_world()
    def test_exclusion_release_and_stale_owner_fencing(self):
        a=SchedulerGuard(self.world).acquire();b=SchedulerGuard(self.world)
        with self.assertRaises(LeaseLost):b.acquire()
        SchedulerLease.objects.filter(world=self.world).update(expires_at=timezone.now()-timedelta(seconds=1))
        b.acquire()
        with self.assertRaises(LeaseLost),a.work():pass
        a.release();self.assertEqual(SchedulerLease.objects.get(world=self.world).owner,b.owner)
        b.release();a.acquire();a.release()
    def test_deleted_world_lease_is_reported_as_lost_not_an_orm_error(self):
        guard=SchedulerGuard(self.world).acquire();SchedulerLease.objects.filter(world=self.world).delete()
        with self.assertRaises(LeaseLost),guard.work():pass
        guard.release()
    @skipUnless(connection.vendor=='sqlite','Local launcher reset uses SQLite')
    def test_local_launcher_reacquires_lease_and_continues_after_real_world_reset(self):
        from unittest.mock import MagicMock,patch
        from pathlib import Path
        from .world_management import reset_world
        from .worlds import current_world
        admin=User.objects.create_superuser('reset-operator',password='Synthetic-Reset-Only-2026')
        old=current_world();clock=[0.];requests=[0]
        server=MagicMock();server.__enter__.return_value=server
        def handle():
            requests[0]+=1;clock[0]+=6
            if requests[0]==1:
                with patch('characters.backups.create_backup',return_value=Path('/private/test-backup')),patch('characters.world_management.seed_clean_world'):
                    reset_world(admin,name='Nowa Kolonia',bot_count=1,password='Synthetic-Reset-Only-2026',confirmation=old.name,expected_world=old.pk)
                    fresh=current_world();fresh.bot_personality_cycles=False;fresh.save(update_fields=['bot_personality_cycles'])
            elif requests[0]>=3:raise KeyboardInterrupt
        server.handle_request.side_effect=handle
        with patch('characters.management.commands.run_colony.make_server',return_value=server),patch('characters.management.commands.run_colony.call_command'),patch('characters.management.commands.run_colony.time.monotonic',side_effect=lambda:clock[0]),patch('characters.management.commands.run_colony.tick_bot',return_value=('mine',True)) as tick:
            call_command('run_colony',bots=1,stdout=StringIO())
        fresh=current_world();self.assertNotEqual(fresh.pk,old.pk);self.assertEqual(fresh.name,'Nowa Kolonia')
        tick.assert_called_once();self.assertEqual(tick.call_args.kwargs['lease'].world_id,fresh.pk)
        self.assertIsNone(SchedulerLease.objects.get(world=fresh).owner)
    def test_standalone_command_refuses_a_live_owner(self):
        with SchedulerGuard(self.world):
            with self.assertRaises(CommandError):call_command('run_bots',rounds=1,limit=1,stdout=StringIO())

@skipUnless(connection.vendor=='postgresql','Requires genuine PostgreSQL row locks')
class PostgreSQLConcurrencyTests(TransactionTestCase):
    reset_sequences=True
    def setUp(self):
        self.seller=User.objects.create_user('seller').playerprofile
        self.a=User.objects.create_user('buyer-a').playerprofile
        self.b=User.objects.create_user('buyer-b').playerprofile
        self.bp=ItemBluePrint.objects.create(name='Miecz testowy',damage=20,base_value=25)
    def race(self,callback):
        gate=Barrier(2)
        def worker(n):
            connections.close_all()
            try:gate.wait(timeout=10);return callback(n)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:return list(pool.map(worker,range(2)))
    def test_fifth_character_slot_has_exactly_one_concurrent_winner(self):
        from django.core.exceptions import ValidationError
        from .character_selection import create_character
        for n in range(2,5):create_character(self.a.user,'Istniejąca '+str(n),self.a.world_id)
        def create(n):
            try:return create_character(User.objects.get(pk=self.a.user_id),'Równoległa '+str(n),self.a.world_id).slot
            except ValidationError:return 0
        self.assertEqual(sorted(self.race(create)),[0,5])
        self.assertEqual(self.a.user.characters.count(),5)

    def test_concurrent_resupply_debits_and_refills_once(self):
        from .camp_privileges import claim_resupply
        from .models import CampSupplyUse,EnergyRefill
        self.a.camp='OLD_CAMP';self.a.guild='GUARD';self.a.current_energy=0;self.a.energy_updated_at=timezone.now();self.a.save()
        key=uuid4()
        results=self.race(lambda n:claim_resupply(PlayerProfile.objects.get(pk=self.a.pk),key).pk)
        self.assertEqual(results[0],results[1]);self.a.refresh_from_db()
        self.assertEqual(self.a.ore_balance,40)
        self.assertEqual(CampSupplyUse.objects.filter(profile=self.a).count(),1)
        self.assertEqual(EnergyRefill.objects.filter(profile=self.a).count(),1)

    def test_single_market_winner_and_conserved_currency(self):
        item=OwnedItem.objects.create(owner=self.seller,blueprint=self.bp,is_market_listed=True,market_price=25)
        total=sum(p.ore_balance for p in (self.seller,self.a,self.b))
        ids=[self.a.pk,self.b.pk]
        result=self.race(lambda n:game.buy_item_on_market(PlayerProfile.objects.get(pk=ids[n]),OwnedItem.objects.get(pk=item.pk)))
        self.assertEqual(sorted(result),[False,True]);self.assertEqual(MarketTrade.objects.count(),1)
        self.assertEqual(sum(PlayerProfile.objects.values_list('ore_balance',flat=True)),total)
    def test_reward_claim_is_paid_once(self):
        from .economy import claim_adventure
        template=AdventureTemplate.objects.create(key='concurrent',name='Patrol',duration_seconds=1,ore_reward=40,experience_reward=1)
        run=AdventureRun.objects.create(profile=self.a,template=template,ends_at=timezone.now()-timedelta(seconds=2),ore_reward=40,experience_reward=1,premium_reward=0)
        before=self.a.ore_balance
        results=self.race(lambda n:claim_adventure(PlayerProfile.objects.get(pk=self.a.pk),run.pk))
        self.assertEqual(sorted(results),[False,True]);self.a.refresh_from_db();self.assertEqual(self.a.ore_balance,before+40)
    def test_premium_purchase_uuid_has_one_debit_and_one_item(self):
        from .economy import purchase_product
        self.a.premium_balance=20;self.a.save()
        product=StoreProduct.objects.create(key='concurrent-sword',name='Miecz',kind='weapon',price=5,blueprint=self.bp)
        key=uuid4()
        rows=self.race(lambda n:purchase_product(PlayerProfile.objects.get(pk=self.a.pk),product.pk,key).pk)
        self.assertEqual(rows[0],rows[1]);self.assertEqual(StorePurchase.objects.count(),1)
        self.a.refresh_from_db();self.assertEqual(self.a.premium_balance,15);self.assertEqual(self.a.inventory.count(),1)
    def test_rank_promotion_spends_once(self):
        from .camp_progression import promote_in_camp
        self.a.camp='OLD_CAMP';self.a.save()
        call_command('seed_story',stdout=StringIO())
        from .testing_story import claimed_milestone
        claimed_milestone(self.a,'prologue-path')
        CampQuest.objects.create(profile=self.a,rank_key='DIGGER',progress={'mine':1})
        result=self.race(lambda n:promote_in_camp(PlayerProfile.objects.get(pk=self.a.pk),'DIGGER'))
        self.assertEqual(sorted(result),[False,True]);self.a.refresh_from_db();self.assertEqual(self.a.guild,'DIGGER')
    def test_two_scheduler_connections_have_one_owner(self):
        from .worlds import current_world
        world=current_world();guards=[SchedulerGuard(world),SchedulerGuard(world)]
        def acquire(n):
            try:guards[n].acquire();return True
            except LeaseLost:return False
        self.assertEqual(sorted(self.race(acquire)),[False,True])
        for guard in guards:guard.release()
    def test_slow_bot_policy_does_not_hold_player_locks_during_human_trade(self):
        from .bots import tick_bot
        self.a.is_bot=True;self.a.bot_role='trader';self.a.save()
        offered=OwnedItem.objects.create(owner=self.seller,blueprint=self.bp,is_market_listed=True,market_price=5)
        bot_offer=OwnedItem.objects.create(owner=self.a,blueprint=self.bp,is_market_listed=True,market_price=5)
        entered=Event();release=Event()
        class SlowPolicy:
            def choose(policy,obs):
                entered.set();release.wait(timeout=10);return 'buy',offered.pk
        def bot():
            connections.close_all()
            try:return tick_bot(PlayerProfile.objects.get(pk=self.a.pk),SlowPolicy(), force_active=True)
            finally:connections.close_all()
        def human():
            connections.close_all()
            try:return game.buy_item_on_market(PlayerProfile.objects.get(pk=self.seller.pk),OwnedItem.objects.get(pk=bot_offer.pk))
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            pending=pool.submit(bot)
            try:
                self.assertTrue(entered.wait(10))
                self.assertTrue(pool.submit(human).result(timeout=8))
            finally:release.set()
            self.assertEqual(pending.result(timeout=10),('buy',True))
        self.assertEqual(MarketTrade.objects.count(),2)

    def test_lock_timeout_is_a_clean_conflict_with_no_resource_loss(self):
        from django.db import transaction
        def blocked():
            connections.close_all()
            try:
                with connection.cursor() as cursor:cursor.execute("SET lock_timeout='100ms'")
                return game.start_mining(PlayerProfile.objects.get(pk=self.a.pk),15)
            finally:connections.close_all()
        with transaction.atomic():
            PlayerProfile.objects.select_for_update().get(pk=self.a.pk)
            with ThreadPoolExecutor(max_workers=1) as pool:self.assertFalse(pool.submit(blocked).result(timeout=5))
        self.a.refresh_from_db();self.assertEqual(self.a.current_energy,100);self.assertIsNone(self.a.action_end_time)
    def test_one_hundred_bots_with_parallel_player_pages(self):
        import time
        from django.test import Client
        from .bots import tick_bot
        from .worlds import current_world
        from .release_probe import record_scenario
        call_command('run_bots',create=100,create_only=True,limit=100,stdout=StringIO())
        world=current_world();guard=SchedulerGuard(world).acquire()
        bot_ids=list(PlayerProfile.objects.filter(is_bot=True).values_list('pk',flat=True))
        players=[User.objects.create_user('load-player-'+str(n)).pk for n in range(4)]
        latencies=[];started=time.monotonic()
        def resident(user_id):
            connections.close_all()
            try:
                client=Client();client.force_login(User.objects.get(pk=user_id))
                for path in ['/','/ekwipunek/','/plac_targowy/','/','/ekwipunek/']:
                    before=time.monotonic();response=client.get(path)
                    self.assertEqual(response.status_code,200);latencies.append(time.monotonic()-before)
            finally:connections.close_all()
        try:
            with ThreadPoolExecutor(max_workers=4) as pool:
                requests=[pool.submit(resident,user_id) for user_id in players]
                for pk in bot_ids:self.assertTrue(tick_bot(PlayerProfile.objects.get(pk=pk),lease=guard, force_active=True)[1])
                for response in requests:response.result(timeout=30)
        finally:guard.release()
        record_scenario('postgresql-100-botow-i-4-graczy',{'bots':100,'player_requests':len(latencies),'elapsed_seconds':round(time.monotonic()-started,3),'http_p95_ms':round(sorted(latencies)[int(len(latencies)*.95)-1]*1000,2),'errors':0})

@skipUnless(connection.vendor=='postgresql','SQLite → PostgreSQL import requires PostgreSQL')
class PostgreSQLImportTests(TransactionTestCase):
    def test_import_preserves_save_microseconds_password_and_sequences_and_refuses_overwrite(self):
        import hashlib,subprocess,sys,tempfile
        from pathlib import Path
        from django.conf import settings
        from ore_empire.database import sqlite_environment
        from .models import BotDecision
        with tempfile.TemporaryDirectory(prefix='ore-import-test-') as tmp:
            source=Path(tmp)/'source.sqlite3';env=sqlite_environment(source)
            proc=subprocess.run([sys.executable,'manage.py','migrate','--noinput'],env=env,cwd=settings.BASE_DIR,capture_output=True)
            self.assertEqual(proc.returncode,0)
            fixture="from django.contrib.auth.models import User; from characters.models import BotDecision; from django.utils import timezone; u=User.objects.create_user('migration-test',password='synthetic-test-password'); p=u.playerprofile; p.ore_balance=789; p.save(); BotDecision.objects.create(profile=p,created_at=timezone.now().replace(microsecond=123456),role='miner',action='wait',success=True,observation={},ore_delta=0,energy_delta=0)"
            proc=subprocess.run([sys.executable,'manage.py','shell','-c',fixture],env=env,cwd=settings.BASE_DIR,capture_output=True)
            self.assertEqual(proc.returncode,0)
            before=hashlib.sha256(source.read_bytes()).hexdigest()
            call_command('import_sqlite_world',source=source,report=Path(tmp)/'proof.json',confirm_empty_target=True,stdout=StringIO())
            user=User.objects.get(username='migration-test')
            self.assertTrue(user.check_password('synthetic-test-password'));self.assertEqual(user.playerprofile.ore_balance,789)
            self.assertEqual(BotDecision.objects.get().created_at.microsecond,123456)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before)
            self.assertGreater(User.objects.create_user('after-migration').pk,user.pk)
            with self.assertRaises(CommandError):call_command('import_sqlite_world',source=source,report=Path(tmp)/'second.json',confirm_empty_target=True,stdout=StringIO())
            self.assertEqual(user.playerprofile.ore_balance,789)
