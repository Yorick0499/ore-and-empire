import io,json,os,shutil,tempfile
from datetime import timedelta
from pathlib import Path
from unittest import skipUnless
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase,TransactionTestCase,SimpleTestCase,override_settings,RequestFactory
from django.utils import timezone
from .models import AuthRateBucket,SchedulerLease,World
from .scheduler_lease import SchedulerGuard

class ProductionSettingsTests(SimpleTestCase):
    def env(self):return {'SECRET_KEY':'test-only-production-configuration-0123456789-abcdefghijklmnopqrstuvwxyz','DEBUG':'False','ALLOWED_HOSTS':'colony.example.test','CSRF_TRUSTED_ORIGINS':'https://colony.example.test'}
    def test_public_profile_refuses_unsafe_settings(self):
        from ore_empire.production import production_settings
        from django.core.exceptions import ImproperlyConfigured
        db={'ENGINE':'django.db.backends.postgresql'}
        config=production_settings(self.env(),db)
        self.assertTrue(config['SESSION_COOKIE_SECURE']);self.assertTrue(config['SECURE_SSL_REDIRECT'])
        for override in ({'DEBUG':'True'},{'SECRET_KEY':'short'},{'ALLOWED_HOSTS':'*'},{'CSRF_TRUSTED_ORIGINS':'http://colony.example.test'},{'CSRF_TRUSTED_ORIGINS':'https://foreign.example.test'}):
            with self.assertRaises(ImproperlyConfigured):production_settings({**self.env(),**override},db)
        with self.assertRaises(ImproperlyConfigured):production_settings(self.env(),{'ENGINE':'django.db.backends.sqlite3'})
    def test_untrusted_forwarded_addresses_cannot_bypass_limits(self):
        from .auth_limits import client_address
        request=RequestFactory().post('/',REMOTE_ADDR='198.51.100.8',HTTP_X_FORWARDED_FOR='203.0.113.1')
        self.assertEqual(client_address(request),'198.51.100.8')
        request.META['REMOTE_ADDR']='127.0.0.1'
        self.assertEqual(client_address(request),'203.0.113.1')

@override_settings(AUTH_RATE_LIMITS={'login':3,'ip':20,'register':2,'window':300})
class AuthenticationAndHealthTests(TestCase):
    def setUp(self):self.user=User.objects.create_user('resident',password='test-only-password')
    def test_login_budget_expiration_and_success(self):
        for _ in range(3):self.assertEqual(self.client.post('/konto/logowanie/',{'username':'resident','password':'wrong'}).status_code,200)
        response=self.client.post('/konto/logowanie/',{'username':'resident','password':'test-only-password'})
        self.assertEqual(response.status_code,429);self.assertGreater(int(response['Retry-After']),0)
        self.assertFalse(any('resident' in value or '127.' in value for value in AuthRateBucket.objects.values_list('key',flat=True)))
        AuthRateBucket.objects.update(window_started=timezone.now()-timedelta(seconds=301))
        self.assertEqual(self.client.post('/konto/logowanie/',{'username':'resident','password':'test-only-password'}).status_code,302)
    def test_signup_limits_and_other_pages_remain_playable(self):
        for _ in range(2):self.assertEqual(self.client.post('/konto/rejestracja/',{}).status_code,200)
        self.assertEqual(self.client.post('/konto/rejestracja/',{}).status_code,429)
        self.assertEqual(self.client.get('/konto/logowanie/').status_code,200)
    def test_admin_login_is_limited_and_public_bootstrap_is_closed(self):
        for _ in range(3):self.client.post('/admin/login/',{'username':'resident','password':'wrong'})
        self.assertEqual(self.client.post('/admin/login/',{'username':'resident','password':'wrong'}).status_code,429)
        with override_settings(PRODUCTION=True):self.assertEqual(self.client.get('/inicjalizacja/').status_code,403)
        self.client.force_login(self.user)
        for path in ('/zarzadca/','/zarzadca/swiat/','/zarzadca/gospodarka/','/zarzadca/swiat/reset/'):
            response=self.client.get(path);self.assertIn(response.status_code,(302,403))
            if response.status_code==302:self.assertTrue('/logowanie/' in response.url or '/admin/login/' in response.url)
    def test_readiness_tracks_database_world_and_lease(self):
        self.assertEqual(self.client.get('/health/live/').status_code,200)
        self.assertEqual(self.client.get('/health/ready/').status_code,503)
        world=self.user.playerprofile.world;world.configured=True;world.bot_count=1;world.save()
        self.assertEqual(self.client.get('/health/ready/').status_code,503)
        with SchedulerGuard(world):
            self.assertEqual(self.client.get('/health/ready/').status_code,200)
            call_command('check_worker',stdout=io.StringIO())
        self.assertEqual(self.client.get('/health/ready/').status_code,503)
        world.bot_count=0;world.save();self.assertEqual(self.client.get('/health/ready/').status_code,200)
    def test_database_unavailable_is_reported_without_exception_details(self):
        from django.db import OperationalError
        with patch('characters.health.connection.cursor',side_effect=OperationalError('private details')):
            response=self.client.get('/health/ready/')
        self.assertEqual(response.status_code,503);self.assertNotIn(b'private',response.content)

@skipUnless(connection.vendor=='postgresql','Native PostgreSQL backup/restore')
class PostgreSQLBackupTests(TransactionTestCase):
    def test_snapshot_restore_preserves_full_logical_state_and_never_replaces_a_database(self):
        from .postgres_backups import create_pg_backup,restore_pg_drill,tool
        import psycopg
        from psycopg import sql
        from uuid import uuid4
        try:tool('pg_dump');tool('pg_restore')
        except ValueError:self.skipTest('Install PostgreSQL client tools')
        user=User.objects.create_user('backup-test',password='test-only-backup-password')
        p=user.playerprofile;p.ore_balance=314;p.save()
        target='ore_drill_'+uuid4().hex[:14];config=settings.DATABASES['default']
        with tempfile.TemporaryDirectory(prefix='ore-pg-backup-test-') as tmp:
            backup=create_pg_backup(tmp)
            self.assertEqual((backup/'world.pgdump').stat().st_mode&0o777,0o600)
            try:
                proof=restore_pg_drill(backup,target);self.assertTrue(proof['migration_applied'])
                with self.assertRaises(Exception):restore_pg_drill(backup,target)
                with self.assertRaises(ValueError):restore_pg_drill(backup,config['NAME'])
                p.refresh_from_db();self.assertEqual(p.ore_balance,314)
                self.assertTrue(user.check_password('test-only-backup-password'))
            finally:
                with psycopg.connect(dbname=config['NAME'],host=config.get('HOST'),port=config.get('PORT'),user=config.get('USER'),password=config.get('PASSWORD'),autocommit=True) as db:db.execute(sql.SQL('DROP DATABASE IF EXISTS {} WITH (FORCE)').format(sql.Identifier(target)))
    def test_old_inventory_dump_migrates_power_and_still_checks_the_full_snapshot(self):
        import hashlib, subprocess, sys
        import psycopg
        from psycopg import sql
        from uuid import uuid4
        from .postgres_backups import pg_env, tool, restore_pg_drill
        from .backups import sha
        from .management.commands.import_sqlite_world import canonical, EXCLUDES
        config=settings.DATABASES['default']
        source='ore_old_'+uuid4().hex[:12];target='ore_new_'+uuid4().hex[:12]
        kwargs=dict(dbname=config['NAME'],host=config.get('HOST'),port=config.get('PORT'),user=config.get('USER'),password=config.get('PASSWORD'),autocommit=True)
        with psycopg.connect(**kwargs) as admin, tempfile.TemporaryDirectory(prefix='ore-old-pg-test-') as tmp:
            root=Path(tmp);admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(source)))
            try:
                env=pg_env(config,source)
                result=subprocess.run([sys.executable,'manage.py','migrate','characters','0036','--noinput'],cwd=settings.BASE_DIR,env=env,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr.decode())
                script="""import os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','ore_empire.settings');import django;django.setup()
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
apps=MigrationExecutor(connection).loader.project_state([('characters','0036_ochrona_rynsztunku')]).apps
U=apps.get_model('auth','User');P=apps.get_model('characters','PlayerProfile');B=apps.get_model('characters','ItemBluePrint');I=apps.get_model('characters','OwnedItem');W=apps.get_model('characters','World')
u=U.objects.create(username='legacy-pg',password='synthetic-old-hash');p=P.objects.create(user=u,world=W.objects.first(),ore_balance=5432);bp=B.objects.create(name='Old blade',damage=20)
I.objects.create(owner=p,blueprint=bp,upgrade_level=10)
from django.utils import timezone
from datetime import timedelta
T=apps.get_model('characters','AdventureTemplate');R=apps.get_model('characters','AdventureRun')
q=T.objects.create(key='courier',name='Dawny meldunek operatora',description='Własny opis',ore_reward=41)
R.objects.create(profile=p,template=q,ends_at=timezone.now()+timedelta(days=1),ore_reward=41,experience_reward=93,premium_reward=0)
from django.core.management import call_command
from characters.management.commands.import_sqlite_world import EXCLUDES,canonical
import io
for app in ['admin','sessions']:call_command('migrate',app,interactive=False,stdout=io.StringIO())
from characters.migration_testing import historical_fixture
print(canonical(historical_fixture(apps,EXCLUDES))[0].decode())
"""
                facts=subprocess.run([sys.executable,'-c',script],cwd=settings.BASE_DIR,env=env,capture_output=True)
                self.assertEqual(facts.returncode,0,facts.stderr.decode())
                logical,counts=canonical(facts.stdout)
                dump=root/'world.pgdump'
                result=subprocess.run([tool('pg_dump'),'--format=custom','--no-owner','--no-acl','--file='+str(dump)],env=env,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr.decode())
                manifest={'schema':1,'engine':'postgresql','database_sha256':sha(dump),'logical_sha256':hashlib.sha256(logical).hexdigest(),'models':counts}
                (root/'manifest.json').write_text(json.dumps(manifest))
                proof=restore_pg_drill(root,target);self.assertTrue(proof['migration_applied'])
                with psycopg.connect(**{**kwargs,'dbname':target}) as restored:
                    self.assertEqual(restored.execute('SELECT rarity,upgrade_level FROM characters_owneditem').fetchone(),(4,2))
                    self.assertEqual(restored.execute('SELECT ore_balance FROM characters_playerprofile').fetchone(),(5432,))
                    self.assertEqual(restored.execute("SELECT briefing->>'name',ore_reward,experience_reward,claimed_at FROM characters_adventurerun").fetchone(),('Dawny meldunek operatora',41,93,None))
            finally:
                for name in [source,target]:admin.execute(sql.SQL('DROP DATABASE IF EXISTS {} WITH (FORCE)').format(sql.Identifier(name)))

    def test_corrupt_dump_is_rejected_before_creating_destination(self):
        from .postgres_backups import restore_pg_drill
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'world.pgdump').write_bytes(b'broken');(root/'manifest.json').write_text(json.dumps({'schema':1,'engine':'postgresql','database_sha256':'wrong'}))
            with self.assertRaises(ValueError):restore_pg_drill(root,'ore_never_created')

@override_settings(PRODUCTION=True,SECURE_SSL_REDIRECT=True,SESSION_COOKIE_SECURE=True,CSRF_COOKIE_SECURE=True,CSRF_TRUSTED_ORIGINS=['https://testserver'])
class SecurePlayerLoopTests(TestCase):
    def test_registration_mining_purchase_equipping_and_battle_over_secure_forms(self):
        from django.test import Client
        from .models import ItemBluePrint
        from uuid import uuid4
        for name in ('seed_world','seed_equipment'):call_command(name,stdout=io.StringIO())
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.get('/konto/rejestracja/',secure=True).status_code,200)
        token=client.cookies['csrftoken'].value
        response=client.post('/konto/rejestracja/',{'username':'secure-player','password1':'Synthetic-Player-Only-2026','password2':'Synthetic-Player-Only-2026','csrfmiddlewaretoken':token},secure=True,HTTP_ORIGIN='https://testserver')
        self.assertEqual(response.status_code,302);self.assertTrue(client.cookies['sessionid']['secure'])
        def post(path,values):
            return client.post(path,{**values,'csrfmiddlewaretoken':client.cookies['csrftoken'].value},secure=True,HTTP_ORIGIN='https://testserver')
        p=User.objects.get(username='secure-player').playerprofile
        now=timezone.now();self.assertEqual(post('/kopalnia/',{'action':'mine'}).status_code,302)
        with patch('django.utils.timezone.now',return_value=now+timedelta(seconds=16)):
            self.assertEqual(post('/kopalnia/',{'action':'claim'}).status_code,302)
            p.refresh_from_db();earned=p.ore_balance
            bp=ItemBluePrint.objects.get(name='Zardzewiały miecz')
            self.assertEqual(post('/sklep/',{'action':'buy','buy_item_id':bp.pk}).status_code,302)
            item=p.inventory.get(blueprint=bp)
            self.assertEqual(post('/ekwipunek/',{'action':'equip','item_id':item.pk}).status_code,302)
            self.assertEqual(post('/polowanie/?location=exchange',{'monster_key':'young_scavenger','request_key':uuid4()}).status_code,302)
            self.assertTrue(p.battles.first().won)
            p.refresh_from_db();self.assertEqual(p.ore_balance,earned-bp.base_value)
        self.assertGreater(p.experience,0)
