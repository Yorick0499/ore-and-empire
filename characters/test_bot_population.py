from collections import Counter
from io import StringIO
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction,IntegrityError
from django.test import TestCase,SimpleTestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from .models import World,PlayerProfile
from .bot_population import DEFAULT_BOTS_PER_WORLD,MAX_BOTS_PER_WORLD
from .bot_scheduler import BotScheduler
from .bot_personalities import due_population
from .world_management import WorldSettingsForm,WorldSetupForm


class PopulationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from .world_management import seed_clean_world
        from .worlds import current_world
        seed_clean_world();cls.colony=current_world();cls.colony.configured=True;cls.colony.bot_count=125;cls.colony.bot_personality_cycles=False;cls.colony.save()
        call_command('run_bots',create=125,create_only=True,stdout=StringIO())
        call_command('open_khorinis',bots=125,stdout=StringIO())
        cls.island=World.objects.get(universe='GOTHIC_II',is_open=True)

    def test_defaults_and_database_limits(self):
        self.assertEqual(World().bot_count,125)
        self.assertEqual(DEFAULT_BOTS_PER_WORLD*2,250)
        self.assertEqual(WorldSetupForm().fields['bot_count'].initial,125)
        self.assertTrue(WorldSettingsForm({'name':'Świat','bot_count':300}).is_valid())
        self.assertFalse(WorldSettingsForm({'name':'Świat','bot_count':301}).is_valid())
        with transaction.atomic():
            with self.assertRaises(IntegrityError):World.objects.filter(pk=self.colony.pk).update(bot_count=301)
        self.assertEqual(PlayerProfile.objects.filter(is_bot=True).count(),250)

    def test_shrinking_and_restoring_population_preserves_all_progress(self):
        people=PlayerProfile.objects.filter(is_bot=True).order_by('pk')
        p=people.filter(world=self.colony).last();p.ore_balance=987;p.level=7;p.save()
        before=list(people.values())
        self.colony.bot_count=40;self.colony.save()
        self.assertEqual(len(due_population(self.colony)),40)
        self.assertEqual(list(people.values()),before)
        self.colony.bot_count=125;self.colony.save()
        call_command('run_bots',world=self.colony.pk,create=125,create_only=True,stdout=StringIO())
        self.assertEqual(len(due_population(self.colony)),125)
        self.assertEqual(list(people.values()),before)

    def test_population_read_has_constant_query_count_at_three_hundred(self):
        self.colony.bot_count=300;self.colony.save()
        call_command('run_bots',world=self.colony.pk,create=300,create_only=True,stdout=StringIO())
        self.assertFalse(PlayerProfile.objects.filter(world=self.colony,is_bot=True,bot_personality='').exists())
        with CaptureQueriesContext(connection) as queries:ids=due_population(self.colony)
        self.assertEqual(len(ids),300);self.assertEqual(len(queries),1)
        self.assertTrue(set(ids).isdisjoint(PlayerProfile.objects.filter(world=self.island).values_list('pk',flat=True)))

    def test_personality_initialization_does_not_write_other_world(self):
        PlayerProfile.objects.filter(world=self.island).update(bot_personality='')
        before=list(PlayerProfile.objects.filter(world=self.island).order_by('pk').values())
        call_command('run_bots',world=self.colony.pk,create_only=True,stdout=StringIO())
        self.assertEqual(list(PlayerProfile.objects.filter(world=self.island).order_by('pk').values()),before)

    def test_legacy_loop_uses_the_shared_adaptive_worker(self):
        with patch('characters.management.commands.run_bots.call_command') as run:
            call_command('run_bots',loop=True,stdout=StringIO())
        self.assertEqual(run.call_args.args,('run_worker',))
        self.assertEqual(run.call_args.kwargs['interval'],5)

    def test_loop_rejects_bounded_limit_before_creating_accounts(self):
        before=PlayerProfile.objects.count()
        with self.assertRaises(CommandError):
            call_command('run_bots',loop=True,limit=300,create=300,stdout=StringIO())
        self.assertEqual(PlayerProfile.objects.count(),before)

    def test_resident_list_is_bounded_and_includes_accounts_after_first_hundred(self):
        user=User.objects.create_user('visitor');self.client.force_login(user)
        response=self.client.get('/zycie-kolonii/?page=5')
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.context['residents']),5)
        self.assertEqual(response.context['resident_page'].paginator.count,125)
        self.assertEqual(response.context['configured_count'],125)
        self.assertEqual(response.context['residents'][-1].pk,PlayerProfile.objects.filter(world=self.colony,is_bot=True).order_by('pk').last().pk)


class LargeSchedulerTests(SimpleTestCase):
    def test_public_names_remain_distinct_for_two_maximum_populations(self):
        # Cover future ID ranges/cycles as well as the current 600 residents.
        names=[PlayerProfile(pk=n,user_id=1,world_id=1,is_bot=True).display_name for n in range(1,10001)]
        self.assertEqual(len({name.casefold() for name in names}),10000)
        self.assertEqual(names[:5],['Gorn243','DiegoxD','XLesterX','IksDex','WhiteCFD'])
        self.assertEqual(names[49],'BandytaNaL4')
        self.assertTrue(all(name.isascii() and len(name)<=30 for name in names))
        self.assertEqual(PlayerProfile(pk=42,user_id=1,world_id=1,is_bot=True).display_name,names[41])

    def test_benchmark_environment_cannot_inherit_a_live_postgres_url(self):
        import os
        from pathlib import Path
        from scripts.benchmark_bots import isolated_environment
        from ore_empire.database import database_config
        url='postgresql://synthetic:synthetic@invalid.example/private'
        with patch.dict(os.environ,{'DATABASE_URL':url,'ORE_DATABASE_ENGINE':'postgresql'}):
            env=isolated_environment(Path('/tmp/ore-benchmark-safety.sqlite3'))
            self.assertEqual(os.environ['DATABASE_URL'],url)
        config=database_config(env,Path('/tmp'))
        self.assertEqual(config['ENGINE'],'django.db.backends.sqlite3')
        self.assertEqual(config['NAME'],'/tmp/ore-benchmark-safety.sqlite3')
        self.assertEqual(env['DATABASE_URL'],'')

    def test_rest_survives_temporary_absence_and_cache_expires(self):
        clock=[0.];s=BotScheduler(clock=lambda:clock[0]);s.population([1,2])
        s.step(lambda pk:('wait',True))
        clock[0]=5;s.population([2]);self.assertIn(1,s.rest_until)
        clock[0]=15;s.population([1]);s.next_tick=0
        self.assertIsNone(s.step(lambda pk:self.fail('Resting bot ticked early')))
        self.assertEqual(s.next_tick,30)
        clock[0]=31;s.population([]);self.assertEqual(s.rest_until,{})

    def test_absent_expired_deadline_cannot_cause_busy_loop(self):
        clock=[20.];s=BotScheduler(clock=lambda:clock[0]);s.population([2]);s.rest_until={1:15,2:40}
        self.assertIsNone(s.step(lambda pk:self.fail('Not due')))
        self.assertEqual(s.next_tick,40)

    def test_three_hundred_residents_share_one_fair_throttled_queue(self):
        clock=[0.];s=BotScheduler(clock=lambda:clock[0]);s.population(range(1,301));seen=[]
        def tick(pk):seen.append(pk);clock[0]+=.01;return 'mine',True
        for n in range(300):
            clock[0]=max(clock[0],s.next_tick);s.step(tick)
            if n%10==0:s.population(range(1,301))
        self.assertEqual(Counter(seen),Counter(range(1,301)))
        self.assertGreaterEqual(clock[0],60)
        clock[0]+=1000;s.step(tick);self.assertIsNone(s.step(tick))


class ImportScaffoldTests(TestCase):
    def test_old_empty_placeholder_is_accepted_but_configured_world_is_not(self):
        from .management.commands.import_sqlite_world import clear_migration_scaffold
        from .models import CampGuild
        world=World.objects.filter(is_current=True).first() or World.objects.create(is_current=True)
        world.bot_count=6;world.save()
        for camp in ('OLD_CAMP','NEW_CAMP','SWAMP_CAMP'):CampGuild.objects.get_or_create(world=world,camp=camp)
        world.configured=True;world.save()
        with self.assertRaises(CommandError):clear_migration_scaffold()
        world.configured=False;world.save()
        clear_migration_scaffold()
        self.assertFalse(World.objects.exists());self.assertFalse(CampGuild.objects.exists())


class PopulationMigrationTests(SimpleTestCase):
    def test_old_population_is_not_replaced_by_new_default(self):
        import sqlite3,subprocess,sys,tempfile
        from pathlib import Path
        from django.conf import settings
        from ore_empire.database import sqlite_environment
        with tempfile.TemporaryDirectory() as tmp:
            database=Path(tmp)/'old.sqlite3';env=sqlite_environment(database);env['DATABASE_URL']=''
            def migrate(target):
                result=subprocess.run([sys.executable,'manage.py','migrate','characters',target,'--noinput'],cwd=settings.BASE_DIR,env=env,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
            migrate('0044')
            with sqlite3.connect(database) as db:db.execute("UPDATE characters_world SET bot_count=47,configured=1,name='Zachowany świat'")
            migrate('0045')
            with sqlite3.connect(database) as db:
                self.assertEqual(db.execute('SELECT bot_count,configured,name FROM characters_world').fetchone(),(47,1,'Zachowany świat'))
