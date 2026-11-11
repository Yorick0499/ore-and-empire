import hashlib,json,subprocess,sys,tempfile
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest import skipUnless
from unittest.mock import patch
from uuid import uuid4
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied,ValidationError
from django.core.management import call_command
from django.test import TransactionTestCase,SimpleTestCase
from django.utils import timezone
from django.db import connection
from . import convergence as service
from .models import World,PlayerProfile,RealmConvergence,ConvergenceEvent,OwnedItem,ItemBluePrint,AdventureRun,AdventureTemplate


class PreparationTests(TransactionTestCase):
    def setUp(self):
        self.colony=World.objects.filter(is_current=True).first() or World.objects.create(is_current=True)
        self.colony.configured=True;self.colony.save()
        self.island=World.objects.create(universe='GOTHIC_II',is_open=True,configured=True)
        self.admin=User.objects.create_user('operator',is_superuser=True,is_staff=True)
        self.user=User.objects.create_user('resident');self.p=self.user.playerprofile
        self.other=PlayerProfile.objects.create(user=self.user,world=self.island,slot=2,name='Wyspiarz')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)

    def plan(self):return service.plan_preparation(self.admin,self.colony.pk,self.island.pk)

    def fake_snapshot(self,root):
        backup=Path(root)/str(uuid4());backup.mkdir(parents=True)
        raw=b'synthetic private backup';(backup/'world.sqlite3').write_bytes(raw)
        digest=hashlib.sha256(raw).hexdigest();proof={'verified_at':'test','tables':3}
        (backup/'manifest.json').write_text(json.dumps({'schema':1,'engine':'sqlite','database_sha256':digest}))
        (backup/'verification.json').write_text(json.dumps(proof))
        return str(backup),digest,{'restore':proof}

    def test_dry_run_reads_both_markets_and_activities_without_writing(self):
        bp=ItemBluePrint.objects.create(name='Towar')
        for p in (self.p,self.other):
            OwnedItem.objects.create(owner=p,blueprint=bp,is_market_listed=True,market_price=10)
            p.action_end_time=timezone.now()+timedelta(minutes=10);p.save()
            q=AdventureTemplate.objects.create(key='contract-'+str(p.pk),name='Praca',universe=p.world.universe)
            AdventureRun.objects.create(profile=p,template=q,ends_at=timezone.now()+timedelta(minutes=20),ore_reward=30,experience_reward=50,premium_reward=1)
        before=list(PlayerProfile.objects.values());items=list(OwnedItem.objects.values());runs=list(AdventureRun.objects.values())
        output=StringIO();call_command('prepare_convergence',colony=self.colony.pk,khorinis=self.island.pk,stdout=output)
        result=json.loads(output.getvalue())
        self.assertEqual((result['market'],result['ranking']),('shared','shared'))
        self.assertEqual((result['market_offers'],result['mining_jobs'],result['unclaimed_adventures']),(2,2,2))
        self.assertFalse(result['activation_available']);self.assertFalse(result['jarkendar_open'])
        self.assertEqual(before,list(PlayerProfile.objects.values()));self.assertEqual(items,list(OwnedItem.objects.values()));self.assertEqual(runs,list(AdventureRun.objects.values()))
        self.assertFalse(RealmConvergence.objects.exists());self.assertFalse(ConvergenceEvent.objects.exists())

    @skipUnless(connection.vendor=='postgresql','Row-lock contention requires PostgreSQL')
    def test_two_workers_claim_exactly_one_attempt(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections
        operation=self.plan();barrier=Barrier(2);admin_id=self.admin.pk
        def worker():
            close_old_connections()
            try:
                operator=User.objects.get(pk=admin_id);barrier.wait(timeout=10)
                try:service.claim_preparation(operator,operation.pk,uuid4());return 'claimed'
                except service.PreparationBusy:return 'busy'
            finally:connection.close()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:worker(),range(2)))
        self.assertCountEqual(results,['claimed','busy'])
        operation.refresh_from_db();self.assertEqual(operation.attempts,1)

    @skipUnless(connection.vendor=='postgresql','Native pg_dump/restore requires PostgreSQL')
    def test_real_postgres_snapshot_restores_and_retry_reuses_proof(self):
        operation=self.plan()
        ready=service.prepare(self.admin,operation.pk,self.tmp.name)
        self.assertEqual(ready.phase,'ready');self.assertEqual(ready.snapshot['engine'],'postgresql')
        service.verify_snapshot(ready)
        again=service.prepare(self.admin,operation.pk,self.tmp.name)
        self.assertEqual(again.attempts,1);self.assertEqual(again.backup_path,ready.backup_path)
        self.p.refresh_from_db();self.assertEqual(self.p.origin_world_id,self.colony.pk)

    def test_origin_stays_when_current_world_changes(self):
        self.assertEqual(self.p.origin_world_id,self.colony.pk)
        self.p.world=self.island;self.p.save(update_fields=['world'])
        self.p.refresh_from_db();self.assertEqual(self.p.origin_world_id,self.colony.pk)

    def test_plan_and_successful_preparation_are_idempotent(self):
        first=self.plan();self.assertEqual(self.plan().pk,first.pk)
        with patch.object(service,'snapshot',side_effect=self.fake_snapshot) as capture:
            ready=service.prepare(self.admin,first.pk,self.tmp.name)
            again=service.prepare(self.admin,first.pk,self.tmp.name)
        self.assertEqual(capture.call_count,1);self.assertEqual(ready.pk,again.pk)
        self.assertEqual(again.phase,'ready');self.assertEqual(again.attempts,1)
        self.assertEqual(first.events.filter(kind='planned').count(),1)
        self.assertEqual(first.events.filter(kind='snapshot_verified').count(),1)
        self.assertEqual(self.p.world_id,self.colony.pk)
        self.assertEqual(World.objects.filter(is_open=True).count(),1)

    def test_failed_backup_is_audited_and_retryable(self):
        operation=self.plan()
        with patch.object(service,'snapshot',side_effect=RuntimeError('private detail')):
            with self.assertRaises(RuntimeError):service.prepare(self.admin,operation.pk,self.tmp.name)
        operation.refresh_from_db();self.assertEqual(operation.phase,'failed');self.assertIsNone(operation.lease_owner)
        self.assertNotIn('private detail',str(list(operation.events.values())))
        with patch.object(service,'snapshot',side_effect=self.fake_snapshot):ready=service.prepare(self.admin,operation.pk,self.tmp.name)
        self.assertEqual(ready.phase,'ready');self.assertEqual(ready.attempts,2)

    def test_expired_worker_cannot_commit_after_successor_takes_over(self):
        operation=self.plan();old=uuid4();new=uuid4()
        service.claim_preparation(self.admin,operation.pk,old)
        with self.assertRaises(service.PreparationBusy):service.claim_preparation(self.admin,operation.pk,new)
        RealmConvergence.objects.filter(pk=operation.pk).update(lease_expires_at=timezone.now()-timedelta(seconds=1))
        claimed,_=service.claim_preparation(self.admin,operation.pk,new)
        self.assertEqual(claimed.attempts,2)
        with self.assertRaises(service.PreparationBusy):service.finish_preparation(operation.pk,old,self.fake_snapshot(Path(self.tmp.name)/'old'))
        ready=service.finish_preparation(operation.pk,new,self.fake_snapshot(Path(self.tmp.name)/'new'))
        self.assertEqual(ready.phase,'ready');self.assertIn('/new/',ready.backup_path)

    def test_pause_during_copy_blocks_publication_and_can_resume(self):
        operation=self.plan()
        def interrupted(root):
            result=self.fake_snapshot(root);service.set_paused(self.admin,operation.pk,True);return result
        with patch.object(service,'snapshot',side_effect=interrupted):failed=service.prepare(self.admin,operation.pk,self.tmp.name)
        self.assertEqual(failed.phase,'failed');self.assertTrue(failed.paused)
        with self.assertRaises(ValidationError):service.prepare(self.admin,operation.pk,self.tmp.name)
        service.set_paused(self.admin,operation.pk,False)
        with patch.object(service,'snapshot',side_effect=self.fake_snapshot):ready=service.prepare(self.admin,operation.pk,self.tmp.name)
        self.assertEqual(ready.phase,'ready')

    def test_corrupt_backup_requires_a_new_verified_attempt(self):
        operation=self.plan()
        with patch.object(service,'snapshot',side_effect=self.fake_snapshot) as capture:
            ready=service.prepare(self.admin,operation.pk,self.tmp.name)
            (Path(ready.backup_path)/'world.sqlite3').write_bytes(b'broken')
            with self.assertRaises(ValidationError):service.verify_snapshot(ready)
            fixed=service.prepare(self.admin,operation.pk,self.tmp.name)
        self.assertEqual(capture.call_count,2);self.assertEqual(fixed.attempts,2)
        self.assertTrue(fixed.events.filter(kind='backup_invalid').exists())

    def test_permissions_closed_worlds_and_invalid_origin_block_preparation(self):
        with self.assertRaises(PermissionDenied):service.plan_preparation(self.user,self.colony.pk,self.island.pk)
        with self.assertRaises(ValidationError):service.dry_run(self.island.pk,self.colony.pk)
        self.island.is_open=False;self.island.save()
        with self.assertRaises(ValidationError):self.plan()
        self.island.is_open=True;self.island.save()
        PlayerProfile.objects.filter(pk=self.p.pk).update(origin_world=None)
        with self.assertRaises(ValidationError):self.plan()
        self.assertFalse(RealmConvergence.objects.exists())


class PreparationMigrationTests(SimpleTestCase):
    def test_old_database_keeps_progress_and_snapshot_restores_on_retry(self):
        from ore_empire.database import sqlite_environment
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);db=root/'world.sqlite3';env=sqlite_environment(db)
            def run(*args):
                r=subprocess.run([sys.executable,'manage.py',*args],cwd=settings.BASE_DIR,env=env,capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stderr);return r.stdout
            run('migrate','characters','0043','--noinput')
            run('shell','-c',"""from django.db import connection
from django.db.migrations.executor import MigrationExecutor
apps=MigrationExecutor(connection).loader.project_state([('characters','0043_rownolegle_khorinis')]).apps
U=apps.get_model('auth','User');W=apps.get_model('characters','World');P=apps.get_model('characters','PlayerProfile')
w=W.objects.get(is_current=True);w.configured=True;w.save()
i=W.objects.create(universe='GOTHIC_II',is_open=True,configured=True)
u=U.objects.create(username='operator',is_superuser=True,is_active=True,password='synthetic-hash')
p=P.objects.create(user=u,world=w,ore_balance=987,experience=12345,level=6,name='Historyczny',slot=1)
P.objects.create(user=u,world=i,ore_balance=432,name='Wyspiarz',slot=2)
from django.utils import timezone
from datetime import timedelta
p.action_end_time=timezone.now()+timedelta(minutes=15);p.save()
B=apps.get_model('characters','ItemBluePrint');I=apps.get_model('characters','OwnedItem');T=apps.get_model('characters','AdventureTemplate');R=apps.get_model('characters','AdventureRun');A=apps.get_model('characters','BossAttempt')
b=B.objects.create(name='Broń historyczna',kind='weapon',damage=20)
I.objects.create(owner=p,blueprint=b,is_market_listed=True,market_price=123,rarity=3,upgrade_level=2)
t=T.objects.create(key='historical',name='Niedokończona wyprawa')
R.objects.create(profile=p,template=t,ends_at=timezone.now()+timedelta(hours=1),ore_reward=35,experience_reward=75,premium_reward=2,briefing={'name':'Stary kontrakt'})
A.objects.create(profile=p,boss_key='crawler_nest',won=True)
""")
            run('migrate','--noinput')
            run('shell','-c',"""from characters.models import PlayerProfile
p=PlayerProfile.objects.get(name='Historyczny');assert (p.ore_balance,p.experience,p.level,p.origin_world_id)==(987,12345,6,p.world_id)
""")
            import sqlite3
            with sqlite3.connect(db) as conn:colony,island=[row[0] for row in conn.execute('SELECT id FROM characters_world ORDER BY id')]
            args=['prepare_convergence','--colony',str(colony),'--khorinis',str(island),'--operator','operator','--directory',str(root/'copies'),'--prepare']
            from .backups import inspect_database
            def protected():return {k:v for k,v in inspect_database(db).items() if k not in {'characters_realmconvergence','characters_convergenceevent'}}
            before=protected()
            first=json.loads(run(*args));second=json.loads(run(*args))
            self.assertTrue(first['backup_valid']);self.assertEqual(first,second);self.assertEqual(first['attempts'],1)
            self.assertEqual(protected(),before)
            with sqlite3.connect(db) as conn:
                self.assertEqual(conn.execute('SELECT ore_balance FROM characters_playerprofile ORDER BY id').fetchall(),[(987,),(432,)])
                self.assertEqual(conn.execute('SELECT password FROM auth_user').fetchone()[0],'synthetic-hash')
