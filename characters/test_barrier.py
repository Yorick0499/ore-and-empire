from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from uuid import uuid4
import json,os,subprocess,sys,tempfile
from pathlib import Path
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connection,connections,transaction,close_old_connections
from django.test import TestCase,TransactionTestCase,SimpleTestCase,skipUnlessDBFeature
from django.utils import timezone
from .models import World,CampGuild,PlayerProfile,StoryQuest,StoryRun,SleeperRace,SleeperSiege,SleeperStrike,SleeperReward,BarrierEvent,OwnedItem,ItemBluePrint
from . import sleeper
from .barrier import travel,region_ids
from .barrier_activation import activate,claim


def fixture():
    from .world_management import seed_clean_world
    from .worlds import current_world
    seed_clean_world();colony=current_world();colony.configured=True;colony.bot_count=0;colony.save()
    call_command('open_khorinis',bots=0,stdout=StringIO())
    island=World.objects.get(universe='GOTHIC_II',is_open=True)
    guild=CampGuild.objects.get(world=colony,camp='OLD_CAMP');guild.level=10;guild.experience=900;guild.save()
    quest=StoryQuest.objects.get(key='ritual-ready');people=[]
    for n in range(3):
        p=User.objects.create_user('contributor'+str(n)).playerprofile
        p.camp='OLD_CAMP';p.guild='GUARD';p.level=35;p.strength=400;p.life=2000;p.current_health=2000;p.current_energy=100;p.save()
        StoryRun.objects.create(profile=p,quest=quest,status='claimed',snapshot={'key':quest.key})
        people.append(p)
    return colony,island,guild,people


class BarrierTests(TestCase):
    def setUp(self):self.colony,self.island,self.guild,self.people=fixture();self.p=self.people[0]
    def siege(self):
        result=sleeper.rally(self.p);self.assertTrue(result);return result
    def won(self):
        siege=self.siege()
        for p in self.people:SleeperStrike.objects.create(siege=siege,profile=p,account=p.user,request_key=uuid4(),damage=10)
        siege.health=1;siege.save()
        SleeperStrike.objects.update(created_at=timezone.now()-timedelta(minutes=2))
        hit=sleeper.strike(self.p,siege.pk,uuid4());self.assertTrue(hit)
        return SleeperRace.objects.get(pk=siege.race_id)
    def join(self):
        race=self.won();key=uuid4();World.objects.filter(pk__in=[self.colony.pk,self.island.pk]).update(union_key=key)
        race.state='joined';race.joined_at=timezone.now();race.save();return race
    def test_eligibility_is_enforced_and_rally_is_idempotent(self):
        self.guild.level=9;self.guild.save();self.assertFalse(sleeper.rally(self.p))
        self.guild.level=10;self.guild.save();a=self.siege();self.assertEqual(sleeper.rally(self.p).pk,a.pk)
        self.p.story_runs.all().delete();self.assertFalse(sleeper.strike(self.p,a.pk,uuid4()))
    def test_cost_retry_and_same_account_cooldown(self):
        siege=self.siege();key=uuid4();hit=sleeper.strike(self.p,siege.pk,key)
        self.assertTrue(hit);self.p.refresh_from_db();self.assertEqual(self.p.current_energy,75)
        self.assertEqual(sleeper.strike(self.p,siege.pk,key).pk,hit.pk)
        alt=PlayerProfile.objects.create(user=self.p.user,slot=2,world=self.colony,camp='OLD_CAMP',guild='GUARD',level=35,strength=400,life=2000,current_health=2000)
        StoryRun.objects.create(profile=alt,quest=StoryQuest.objects.get(key='ritual-ready'),status='claimed',snapshot={'key':'ritual-ready'})
        self.assertFalse(sleeper.strike(alt,siege.pk,uuid4()))
        self.assertFalse(sleeper.strike(alt,siege.pk,key))
        self.assertEqual(SleeperStrike.objects.count(),1)
    def test_three_accounts_are_required_and_single_account_cannot_break_seal(self):
        siege=self.siege();self.p.strength=100000;self.p.save()
        self.assertTrue(sleeper.strike(self.p,siege.pk,uuid4()));siege.refresh_from_db()
        self.assertEqual(siege.health,80000);self.assertEqual(SleeperRace.objects.get(pk=siege.race_id).state,'racing')
        SleeperStrike.objects.update(created_at=timezone.now()-timedelta(minutes=2));self.p.refresh_from_db();energy=self.p.current_energy
        self.assertFalse(sleeper.strike(self.p,siege.pk,uuid4()));self.p.refresh_from_db();self.assertEqual(self.p.current_energy,energy)
        self.assertTrue(sleeper.card(self.p)['seal_blocked'])
    def test_winner_is_durable_and_other_camp_cannot_finish(self):
        race=self.won();self.assertEqual(race.state,'pending');self.assertEqual(race.winner_id,self.guild.pk)
        self.assertEqual(BarrierEvent.objects.filter(race=race,kind='victory').count(),1)
        self.assertFalse(sleeper.strike(self.people[1],race.sieges.get().pk,uuid4()))
        self.assertFalse(sleeper.claim_reward(self.p))
    def test_failed_strike_rolls_back_health_energy_and_victory(self):
        siege=self.siege();before=siege.health
        with patch.object(SleeperStrike.objects,'create',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):sleeper.strike(self.p,siege.pk,uuid4())
        siege.refresh_from_db();self.p.refresh_from_db()
        self.assertEqual((siege.health,self.p.current_energy),(before,100))
    def test_joined_reward_once_per_account_and_rollback(self):
        race=self.join()
        with patch('characters.economy.change_premium',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):sleeper.claim_reward(self.p)
        self.assertFalse(SleeperReward.objects.exists())
        self.assertTrue(sleeper.claim_reward(self.p));self.p.refresh_from_db();balance=self.p.ore_balance
        self.assertTrue(sleeper.claim_reward(self.p));self.p.refresh_from_db();self.assertEqual(self.p.ore_balance,balance)
        self.assertEqual(SleeperReward.objects.count(),1)
    def test_regions_market_creator_and_history_are_preserved(self):
        from .character_selection import CharacterForm,create_character
        from .game_logic import buy_item_on_market
        from .market_browse import browse_market
        foreign=User.objects.create_user('islander').playerprofile;foreign.world=self.island;foreign.save()
        item=OwnedItem.objects.create(owner=foreign,blueprint=ItemBluePrint.objects.filter(tradeable=True).first(),is_market_listed=True,market_price=1)
        self.assertFalse(buy_item_on_market(self.p,item,1))
        self.join();self.assertEqual(set(region_ids(self.colony)),{self.colony.pk,self.island.pk})
        self.assertEqual(CharacterForm().fields['world'].queryset.count(),1)
        self.assertTrue(buy_item_on_market(self.p,item,1));item.refresh_from_db();self.assertEqual(item.owner_id,self.p.pk)
        old=list(self.p.story_runs.values('id','snapshot','status'));origin=self.p.origin_world_id
        self.assertTrue(travel(self.p,self.island.pk));self.p.refresh_from_db()
        self.assertEqual(self.p.world_id,self.colony.pk);self.assertEqual(self.p.origin_world_id,origin)
        self.assertEqual(list(self.p.story_runs.values('id','snapshot','status')),old)
        self.p.action_end_time=timezone.now()+timedelta(minutes=1);self.p.save();self.assertFalse(travel(self.p,self.colony.pk))
    def test_dragon_and_post_barrier_story_are_gated(self):
        from .post_barrier import seed
        from .story_quests import available
        from .locations import BY_KEY
        seed();quest=StoryQuest.objects.get(key='barrier-new-road')
        self.assertFalse(available(self.p,quest));self.assertFalse(BY_KEY['k2_dragon_fire'].accessible(self.p))
        self.join();self.assertTrue(available(self.p,quest));travel(self.p,self.island.pk)
        self.assertFalse(BY_KEY['k2_dragon_fire'].accessible(self.p))
        travel(self.p,self.colony.pk);self.assertTrue(BY_KEY['k2_dragon_fire'].accessible(self.p))
    def test_ui_and_combined_rankings(self):
        self.join();self.client.force_login(self.p.user)
        for route in ['/bariera/','/wspolnota/','/rankingi/']:
            r=self.client.get(route)
            self.assertEqual(r.status_code,200)
    def test_no_travel_before_merge_or_to_third_world(self):
        self.assertFalse(travel(self.p,self.island.pk));self.join()
        third=World.objects.create(name='Archiwum');self.assertFalse(travel(self.p,third.pk))
    def test_live_lease_and_pause_do_not_activate(self):
        race=self.won();race.paused=True;race.save();self.assertIsNone(claim(race.pk,uuid4()))
        race.paused=False;race.save();owner=uuid4();self.assertTrue(claim(race.pk,owner));self.assertIsNone(claim(race.pk,uuid4()))
        self.client.force_login(self.p.user);self.assertEqual(self.client.get('/bariera/').status_code,503)


class ActivationTests(TransactionTestCase):
    def setUp(self):
        self.colony,self.island,self.guild,self.people=fixture()
        siege=sleeper.rally(self.people[0]);self.race=SleeperRace.objects.get(pk=siege.race_id)
        for p in self.people:SleeperStrike.objects.create(siege=siege,profile=p,account=p.user,request_key=uuid4(),damage=20,created_at=timezone.now()-timedelta(minutes=2))
        siege.health=1;siege.save();self.assertTrue(sleeper.strike(self.people[0],siege.pk,uuid4()))
    def test_atomic_activation_preserves_profiles_and_retries_without_new_backup(self):
        before=list(PlayerProfile.objects.order_by('pk').values())
        with patch('characters.barrier_activation.fresh_snapshot',return_value=('/private/backup','a'*64,{'restore':{'verified':True}})) as backup:
            self.assertTrue(activate(self.race.pk));self.assertTrue(activate(self.race.pk));self.assertEqual(backup.call_count,1)
        self.assertEqual(list(PlayerProfile.objects.order_by('pk').values()),before)
        self.assertEqual(BarrierEvent.objects.filter(race=self.race,kind='joined').count(),1)
        self.assertEqual(World.objects.filter(union_key__isnull=False).count(),2)
    def test_failure_is_rolled_back_and_expired_worker_can_resume(self):
        with patch('characters.barrier_activation.fresh_snapshot',side_effect=RuntimeError):self.assertFalse(activate(self.race.pk))
        self.race.refresh_from_db();self.assertEqual(self.race.state,'failed');self.assertFalse(World.objects.filter(union_key__isnull=False).exists())
        self.assertFalse(activate(self.race.pk)) # backoff
        SleeperRace.objects.filter(pk=self.race.pk).update(lease_expires_at=timezone.now()-timedelta(seconds=1))
        with patch('characters.barrier_activation.fresh_snapshot',return_value=('/private/new','b'*64,{})):self.assertTrue(activate(self.race.pk))
        self.assertEqual(BarrierEvent.objects.filter(race=self.race,kind='victory').count(),1)
    def test_lease_expiry_during_backup_does_not_open_regions(self):
        def expired(root):
            SleeperRace.objects.filter(pk=self.race.pk).update(lease_expires_at=timezone.now()-timedelta(seconds=1));return '/private/old','c'*64,{}
        with patch('characters.barrier_activation.fresh_snapshot',side_effect=expired):self.assertFalse(activate(self.race.pk))
        self.assertFalse(World.objects.filter(union_key__isnull=False).exists())
    def test_restart_after_claim_resumes_same_victory(self):
        owner=uuid4();claim(self.race.pk,owner)
        SleeperRace.objects.filter(pk=self.race.pk).update(lease_expires_at=timezone.now()-timedelta(seconds=1))
        with patch('characters.barrier_activation.fresh_snapshot',return_value=('/private/new','d'*64,{})):self.assertTrue(activate(self.race.pk))
        self.assertEqual(BarrierEvent.objects.filter(race=self.race,kind='victory').count(),1)
    @skipUnlessDBFeature('has_select_for_update')
    def test_postgres_snapshot_restore_and_activation(self):
        if connection.vendor!='postgresql':self.skipTest('PostgreSQL required')
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(activate(self.race.pk,Path(tmp)))
            self.race.refresh_from_db();self.assertTrue(self.race.proof['restore']);self.assertEqual(self.race.state,'joined')


@skipUnlessDBFeature('has_select_for_update')
class SleeperConcurrencyTests(TransactionTestCase):
    def setUp(self):self.colony,self.island,self.guild,self.people=fixture()
    def race_calls(self,calls):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        gate=Barrier(len(calls))
        def execute(call):
            close_old_connections()
            try:gate.wait(timeout=10);return call()
            # Healthy CONN_MAX_AGE connections also belong to this finished thread.
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=len(calls)) as pool:return list(pool.map(execute,calls))
    def test_two_camps_final_strikes_choose_one_winner(self):
        first=sleeper.rally(self.people[0]);enemy=self.people[1];enemy.camp='NEW_CAMP';enemy.guild='MERC';enemy.save()
        guild=CampGuild.objects.get(world=self.colony,camp='NEW_CAMP');guild.level=10;guild.save()
        # Rally permissions and preparation are shared, historical prologue remains.
        second=sleeper.rally(enemy);self.assertTrue(second)
        for siege in (first,second):
            for p in self.people:SleeperStrike.objects.create(siege=siege,profile=p,account=p.user,request_key=uuid4(),damage=1,created_at=timezone.now()-timedelta(minutes=2))
            siege.health=1;siege.save()
        results=self.race_calls([lambda:sleeper.strike(PlayerProfile.objects.get(pk=self.people[0].pk),first.pk,uuid4()),lambda:sleeper.strike(PlayerProfile.objects.get(pk=enemy.pk),second.pk,uuid4())])
        self.assertEqual(sum(bool(x) for x in results),1)
        race=SleeperRace.objects.get(colony=self.colony);self.assertEqual(race.state,'pending')
        self.assertEqual(BarrierEvent.objects.filter(race=race,kind='victory').count(),1)
    def test_two_characters_share_the_account_cooldown(self):
        siege=sleeper.rally(self.people[0]);p=self.people[0]
        alt=PlayerProfile.objects.create(user=p.user,slot=2,world=self.colony,camp='OLD_CAMP',guild='GUARD',level=35,strength=400,life=2000,current_health=2000)
        StoryRun.objects.create(profile=alt,quest=StoryQuest.objects.get(key='ritual-ready'),status='claimed',snapshot={'key':'ritual-ready'})
        results=self.race_calls([lambda:sleeper.strike(PlayerProfile.objects.get(pk=p.pk),siege.pk,uuid4()),lambda:sleeper.strike(PlayerProfile.objects.get(pk=alt.pk),siege.pk,uuid4())])
        self.assertEqual(sum(bool(x) for x in results),1);self.assertEqual(SleeperStrike.objects.filter(siege=siege).count(),1)


class RealSQLiteActivationTests(SimpleTestCase):
    def test_real_snapshot_drill_and_preserved_active_records(self):
        from ore_empire.database import sqlite_environment
        code='''
import django,json
from pathlib import Path
django.setup()
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
from uuid import uuid4
from characters.test_barrier import fixture
from characters.models import *
from characters import sleeper
from characters.barrier_activation import activate
from characters.economy import start_adventure
from characters.barrier import travel
from characters.game_logic import start_mining
call_command('migrate',interactive=False,verbosity=0)
c,i,g,people=fixture();p=people[0];s=sleeper.rally(p)
for actor in people:SleeperStrike.objects.create(siege=s,profile=actor,account=actor.user,request_key=uuid4(),damage=20,created_at=timezone.now()-timedelta(minutes=2))
s.health=1;s.save();assert sleeper.strike(p,s.pk,uuid4())
assert start_mining(people[1],60)
t=AdventureTemplate.objects.filter(universe=i.universe,enabled=True).first()
islander=User.objects.create_user('busy-islander').playerprofile;islander.world=i;islander.save();assert start_adventure(islander,t.pk)
bp=ItemBluePrint.objects.filter(tradeable=True).first();item=OwnedItem.objects.create(owner=p,blueprint=bp,is_market_listed=True,market_price=17)
before={m.__name__:list(m.objects.order_by('pk').values()) for m in (PlayerProfile,OwnedItem,AdventureRun,PremiumEntry,EconomicEntry,StoryRun,User)}
assert activate(s.race_id,Path(__import__('os').environ['BARRIER_TEST_ROOT']))
assert before=={m.__name__:list(m.objects.order_by('pk').values()) for m in (PlayerProfile,OwnedItem,AdventureRun,PremiumEntry,EconomicEntry,StoryRun,User)}
r=SleeperRace.objects.get(pk=s.race_id);assert r.proof['restore'];assert activate(r.pk)
assert BarrierEvent.objects.filter(kind='joined').count()==1
print('REAL_SQLITE_ACTIVATION_OK')
'''
        with tempfile.TemporaryDirectory() as tmp:
            database=Path(tmp)/'source.sqlite3';env=sqlite_environment(database);env.update(DATABASE_URL='',DJANGO_SETTINGS_MODULE='ore_empire.settings',BARRIER_TEST_ROOT=str(Path(tmp)/'backups'))
            result=subprocess.run([sys.executable,'-c',code],cwd=settings.BASE_DIR,env=env,capture_output=True,text=True,timeout=120)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertIn('REAL_SQLITE_ACTIVATION_OK',result.stdout)

class BarrierBotTests(TestCase):
    def test_bot_uses_the_same_sleeper_strike_service(self):
        colony,island,guild,people=fixture();p=people[0];siege=sleeper.rally(p)
        p.is_bot=True;p.bot_turn=13;p.save()
        from .bots import tick_bot
        action,success=tick_bot(p,force_active=True)
        self.assertEqual((action,success),('sleeper_strike',True))
        self.assertEqual(SleeperStrike.objects.filter(profile=p,siege=siege).count(),1)

class MercenaryUnionTests(TransactionTestCase):
    def test_shared_treasury_projects_ranks_and_old_rewards_survive(self):
        from .barrier import guild_for,alliance_card,promote_alliance
        from .camp_guilds import donate_to_camp
        from .camp_raids import rally_camp_raid,strike_camp_raid,claim_camp_raid
        from .post_barrier import seed
        c,i,g,people=fixture();p=people[0]
        onar=User.objects.create_user('onar-contributor').playerprofile
        onar.world=i;onar.camp='ONAR_MERCS';onar.guild='ONAR_MERC';onar.level=40;onar.life=2000;onar.current_health=2000;onar.strength=1000;onar.save()
        # Use the actual last historical rank (tier 3), not an invented rank code.
        from .camp_progression import RANKS
        onar.guild=next(r.key for r in RANKS if r.camp=='ONAR_MERCS' and r.tier==3);onar.save()
        historical=CampGuild.objects.get(world=i,camp='ONAR_MERCS');historical.treasury=200;historical.supply_level=3;historical.save()
        lee=CampGuild.objects.get(world=c,camp='NEW_CAMP');lee.treasury=100;lee.save()
        oldraid=rally_camp_raid(onar);self.assertTrue(oldraid)
        oldraid.health=1;oldraid.save();self.assertTrue(strike_camp_raid(onar,oldraid.pk,uuid4()))
        s=sleeper.rally(p)
        for actor in people:SleeperStrike.objects.create(siege=s,profile=actor,account=actor.user,request_key=uuid4(),damage=1,created_at=timezone.now()-timedelta(minutes=2))
        s.health=1;s.save();sleeper.strike(p,s.pk,uuid4())
        total=sum(CampGuild.objects.values_list('treasury',flat=True))
        with patch('characters.barrier_activation.fresh_snapshot',return_value=('/private/new','e'*64,{})):self.assertTrue(activate(s.race_id))
        self.assertEqual(sum(CampGuild.objects.values_list('treasury',flat=True)),total)
        self.assertEqual(guild_for(onar).camp,'MERCENARIES');self.assertEqual(guild_for(onar).supply_level,3)
        self.assertTrue(claim_camp_raid(onar,oldraid.pk));self.assertTrue(donate_to_camp(onar,10,uuid4()))
        onar.refresh_from_db();self.assertEqual(onar.camp,'ONAR_MERCS');self.assertEqual(onar.camp_tier,3)
        onar.ore_balance=2000;onar.save();seed();q=StoryQuest.objects.get(key='barrier-fire-dragon')
        self.assertFalse(promote_alliance(onar,3))
        StoryRun.objects.create(profile=onar,quest=q,status='claimed',snapshot={'key':q.key})
        oldguild=onar.guild;self.assertTrue(promote_alliance(onar,3));onar.refresh_from_db()
        self.assertEqual((onar.alliance_rank,onar.camp_tier,onar.guild),(4,4,oldguild));self.assertFalse(promote_alliance(onar,3))

class DragonBuildTests(TestCase):
    def test_prepared_post_barrier_melee_archer_and_mage_can_win(self):
        from .bosses import BOSSES
        from .magic import MagicPlan,BY_KEY
        from .game_logic import simulate_combat
        for build in ('warrior','archer','mage'):
            p=User.objects.create_user('dragon-'+build).playerprofile
            p.level=35;p.strength=310 if build=='warrior' else 100;p.dexterity=310 if build=='archer' else 10
            p.life=2500;p.current_health=2500;p.mana=800;p.current_mana=800;p.weapon_prot=100;p.fire_prot=100;p.magic_prot=75;p.save()
            plan=MagicPlan(BY_KEY['icewave'],None,False,1) if build=='mage' else None
            if not plan:
                bp=ItemBluePrint.objects.create(name='Prepared '+build,damage=90,weapon_type='bow' if build=='archer' else 'onehand',damage_type='arrow' if build=='archer' else 'weapon')
                OwnedItem.objects.create(owner=p,blueprint=bp,is_equipped=True,equipped_slot='weapon')
            with patch('characters.game_logic.random.randint',return_value=100):result=simulate_combat(p,'k2_dragon_fire',monster=BOSSES['k2_dragon_fire'].monster,magic_plan=plan)
            self.assertTrue(result.won,(build,result.log[-4:]));self.assertGreater(result.remaining_health,0)

class RestoreEnvironmentTests(SimpleTestCase):
    def test_explicit_restore_targets_cannot_inherit_live_database_url(self):
        from ore_empire.database import sqlite_environment,database_config
        from .postgres_backups import pg_env
        with patch.dict(os.environ,{'DATABASE_URL':'postgresql://private:private@invalid.example/live'}):
            sqlite=sqlite_environment('/tmp/synthetic-restore.sqlite3')
            pg=pg_env({'NAME':'live','USER':'synthetic','PASSWORD':'synthetic','HOST':'127.0.0.1'},'isolated_drill')
        self.assertEqual(sqlite['DATABASE_URL'],'');self.assertEqual(pg['DATABASE_URL'],'')
        self.assertEqual(database_config(sqlite,Path('/tmp'))['NAME'],'/tmp/synthetic-restore.sqlite3')
        self.assertEqual(database_config(pg,Path('/tmp'))['NAME'],'isolated_drill')

class AllianceRetryTests(TestCase):
    def test_stale_promotion_cannot_purchase_next_rank(self):
        from .barrier import promote_alliance
        from .post_barrier import seed
        c,i,g,people=fixture();p=people[0];p.camp='NEW_CAMP';p.guild='MERC';p.level=40;p.ore_balance=5000;p.save()
        key=uuid4();World.objects.filter(pk__in=[c.pk,i.pk]).update(union_key=key);seed()
        for q in StoryQuest.objects.filter(universe='JOINED'):StoryRun.objects.create(profile=p,quest=q,status='claimed',snapshot={'key':q.key})
        self.assertTrue(promote_alliance(p,2));p.refresh_from_db();balance=p.ore_balance
        self.assertFalse(promote_alliance(p,2));p.refresh_from_db();self.assertEqual((p.camp_tier,p.ore_balance),(3,balance))

@skipUnlessDBFeature('has_select_for_update')
class ActivationContentionTests(TransactionTestCase):
    setUp=ActivationTests.setUp
    # Reuse the fixture without repeating the five activation tests.
    def test_unwrapped_writer_cannot_cross_the_snapshot_fence(self):
        from threading import Thread,Event
        from django.db.models import F
        started=Event();finished=Event();errors=[];p=self.people[0];before=PlayerProfile.objects.get(pk=p.pk).ore_balance
        def writer():
            close_old_connections()
            try:
                started.set();PlayerProfile.objects.filter(pk=p.pk).update(ore_balance=F('ore_balance')+7)
            except Exception as exc:errors.append(type(exc).__name__)
            finally:connections.close_all();finished.set()
        thread=Thread(target=writer,daemon=True)
        def snapshot(root):
            thread.start();self.assertTrue(started.wait(2));self.assertFalse(finished.wait(.2));return '/private/new','f'*64,{}
        with patch('characters.barrier_activation.fresh_snapshot',side_effect=snapshot):self.assertTrue(activate(self.race.pk))
        thread.join(timeout=10);self.assertTrue(finished.is_set());self.assertEqual(errors,[])
        self.assertEqual(PlayerProfile.objects.get(pk=p.pk).ore_balance,before+7)
    def test_competing_activators_publish_one_snapshot_and_transition(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        gate=Barrier(2)
        def execute(n):
            close_old_connections()
            try:gate.wait(timeout=10);return activate(self.race.pk)
            finally:connections.close_all()
        with patch('characters.barrier_activation.fresh_snapshot',return_value=('/private/new','f'*64,{})) as backup:
            with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(execute,range(2)))
        self.assertTrue(any(results));self.assertEqual(backup.call_count,1);self.assertEqual(BarrierEvent.objects.filter(race=self.race,kind='joined').count(),1)
