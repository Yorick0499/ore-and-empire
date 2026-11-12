"""Actual fights, capped income, weekly cooperation and saved legacy progress."""
from datetime import timedelta,datetime
from io import StringIO
from uuid import uuid4
from unittest.mock import patch
from django.core.management import call_command
from django.test import TestCase,SimpleTestCase,TransactionTestCase,skipUnlessDBFeature
from django.utils import timezone
from .models import PlayerProfile,World,FrontierProgress,FrontierRecord,RegionalFrontierProgress,CampRaidReward,CampRaidStrike,CampRaid
from .test_faction_succession import fixture,person,succeed
from .testing_story import claimed_milestone
from . import game_logic as game
from .frontier import patrol,board
from .regional_endgame import TRACKS,unlocked,week_start,rewarded_today,DAILY_REWARDS
from .barrier import travel

class RegionalEndgameTests(TestCase):
    def setUp(self):
        self.c,self.i,self.race=fixture();call_command('seed_khorinis',stdout=StringIO());self.p=person(self.c,'OLD_CAMP','BARON');self.p.level=50;self.p.life=2000;self.p.current_health=2000;self.p.strength=800;self.p.ore_balance=50000;self.p.save();succeed(self.race)
        for key in ('nk-undead','nk-sailing','jark-portal'):claimed_milestone(self.p,key)
        self.p=PlayerProfile.objects.get(pk=self.p.pk)
    def ready(self):
        FrontierProgress.objects.filter(profile=self.p).update(last_attempt_at=timezone.now()-timedelta(minutes=6));self.p.current_energy=100;self.p.current_health=self.p.max_health;self.p.save();self.p.refresh_from_db()
    def region_for(self,track):self.assertTrue(travel(self.p,self.c.pk if track=='valley' else self.i.pk))
    def test_four_paths_use_real_combat_and_do_not_rewrite_legacy_progress(self):
        FrontierProgress.objects.create(profile=self.p,unlocked=37,wins=90)
        for track in TRACKS:
            self.ready();self.region_for(track);row=patrol(self.p,1,uuid4(),track);self.assertTrue(row.won,(track,row.snapshot))
            self.assertEqual(row.track,track);self.assertEqual(row.snapshot['entry_fee'],12);self.assertEqual(row.snapshot['version'],2)
            self.assertEqual(RegionalFrontierProgress.objects.get(profile=self.p,track=track).unlocked,2)
        self.assertEqual(FrontierProgress.objects.get(profile=self.p).unlocked,37);self.assertEqual(FrontierProgress.objects.get(profile=self.p).wins,90)
        self.assertEqual(list(board(self.c))[0]['points'],40)
        self.assertEqual(list(board(self.i,'valley'))[0]['points'],10)
    def test_story_barrier_region_portal_and_pending_faction_gates(self):
        self.assertFalse(patrol(self.p,1,uuid4(),'khorinis'))
        self.region_for('jarkendar');self.p.story_runs.filter(quest__key='jark-portal').delete();self.p=PlayerProfile.objects.get(pk=self.p.pk);self.assertFalse(patrol(self.p,1,uuid4(),'jarkendar'))
        self.p.story_runs.filter(quest__key='nk-undead').delete();self.p=PlayerProfile.objects.get(pk=self.p.pk);self.assertFalse(unlocked(self.p));self.assertFalse(patrol(self.p,1,uuid4(),'khorinis'))
        claimed_milestone(self.p,'nk-undead');self.p.faction_membership.faction='PENDING';self.p.faction_membership.save();self.p=PlayerProfile.objects.get(pk=self.p.pk);self.assertFalse(unlocked(self.p))
        World.objects.filter(pk__in=[self.c.pk,self.i.pk]).update(union_key=None);self.assertFalse(patrol(self.p,1,uuid4(),'khorinis'))
    def test_global_cooldown_replay_and_forged_track_do_not_spend_twice(self):
        self.region_for('khorinis');key=uuid4();row=patrol(self.p,1,key,'khorinis');self.p.refresh_from_db();before=(self.p.ore_balance,self.p.current_energy,self.p.experience)
        self.assertEqual(patrol(self.p,1,key,'khorinis').pk,row.pk);self.assertFalse(patrol(self.p,1,key,'irdorath'));self.assertFalse(patrol(self.p,1,uuid4(),'irdorath'));self.assertFalse(patrol(self.p,1,uuid4(),'legacy'));self.assertFalse(patrol(self.p,1,uuid4(),'made-up'))
        self.p.refresh_from_db();self.assertEqual(before,(self.p.ore_balance,self.p.current_energy,self.p.experience))
    def test_daily_reward_budget_shared_between_paths_and_reset_preserves_progress(self):
        now=datetime(2026,11,12,12,tzinfo=timezone.get_current_timezone())
        with patch('django.utils.timezone.now',return_value=now):
            for n in range(DAILY_REWARDS):
                self.ready();track=('khorinis','jarkendar','irdorath')[n%3];self.region_for(track);self.assertTrue(patrol(self.p,1,uuid4(),track).snapshot['rewarded'])
            self.assertEqual(rewarded_today(self.p),8);self.ready();before=self.p.ore_balance;xp=self.p.experience;items=self.p.inventory.count()
            row=patrol(self.p,1,uuid4(),'khorinis');self.assertTrue(row.won);self.assertFalse(row.snapshot['rewarded']);self.assertEqual(row.snapshot['loot'],[]);self.p.refresh_from_db();self.assertEqual((self.p.ore_balance,self.p.experience,self.p.inventory.count()),(before-12,xp,items))
        with patch('django.utils.timezone.now',return_value=now+timedelta(days=1)):
            self.assertEqual(rewarded_today(self.p),0);self.assertEqual(RegionalFrontierProgress.objects.get(profile=self.p,track='khorinis').unlocked,2)
    def test_reward_counter_uses_polish_midnight_after_dst_change(self):
        from datetime import timezone as utc
        now=datetime(2026,3,29,22,30,tzinfo=utc.utc)
        for n in range(9):
            FrontierRecord.objects.create(profile=self.p,request_key=uuid4(),track='khorinis',depth=1,season='2026-03',won=True,points=10,snapshot={'rewarded':True},created_at=datetime(2026,3,29,22,1,tzinfo=utc.utc) if n<8 else datetime(2026,3,29,21,59,tzinfo=utc.utc))
        with patch('django.utils.timezone.now',return_value=now):
            self.assertEqual(rewarded_today(self.p),8);self.assertEqual(week_start().isoformat(),'2026-03-30')
    def test_failed_storage_rolls_back_fee_loot_energy_and_progress(self):
        self.region_for('khorinis');before=(self.p.ore_balance,self.p.current_energy,self.p.inventory.count())
        with patch('characters.frontier.FrontierRecord.objects.create',side_effect=RuntimeError('store')):
            with self.assertRaises(RuntimeError):patrol(self.p,1,uuid4(),'khorinis')
        self.p.refresh_from_db();self.assertEqual(before,(self.p.ore_balance,self.p.current_energy,self.p.inventory.count()));self.assertFalse(RegionalFrontierProgress.objects.filter(profile=self.p).exists())
    def test_weekly_and_daily_raid_coexist_and_weekly_reward_is_once(self):
        from .camp_raids import rally_camp_raid,strike_camp_raid,claim_camp_raid
        self.region_for('khorinis');weekly=rally_camp_raid(self.p,'weekly');self.assertEqual(weekly.day,week_start());self.assertEqual(rally_camp_raid(self.p,'weekly').pk,weekly.pk)
        daily=rally_camp_raid(self.p);self.assertNotEqual(daily.pk,weekly.pk)
        for n in range(50):
            weekly.refresh_from_db()
            if weekly.completed_at:break
            self.ready();CampRaidStrike.objects.filter(raid=weekly).update(created_at=timezone.now()-timedelta(minutes=2));self.assertTrue(strike_camp_raid(self.p,weekly.pk,uuid4()))
        weekly.refresh_from_db();self.assertIsNotNone(weekly.completed_at);self.p.refresh_from_db();before=(self.p.ore_balance,self.p.experience,self.p.premium_balance)
        self.assertTrue(claim_camp_raid(self.p,weekly.pk));self.p.refresh_from_db();self.assertEqual((self.p.ore_balance-before[0],self.p.experience-before[1],self.p.premium_balance-before[2]),(100,1000,0))
        dust=self.p.inventory.filter(blueprint__catalog_key='rune-dust').first().quantity;self.assertTrue(claim_camp_raid(self.p,weekly.pk));self.assertEqual(self.p.inventory.filter(blueprint__catalog_key='rune-dust').first().quantity,dust);self.assertEqual(CampRaidReward.objects.filter(raid=weekly).count(),1)
        with patch('django.utils.timezone.now',return_value=timezone.now()+timedelta(days=7)):
            nxt=rally_camp_raid(self.p,'weekly');self.assertNotEqual(nxt.pk,weekly.pk);self.assertFalse(strike_camp_raid(self.p,weekly.pk,uuid4()))
    def test_post_redirect_and_cooldown_page_work_with_existing_records(self):
        self.client.force_login(self.p.user);self.region_for('khorinis');key=uuid4()
        response=self.client.post('/warty/',{'track':'khorinis','depth':1,'request_key':key})
        self.assertRedirects(response,'/warty/?track=khorinis');page=self.client.get(response.url)
        self.assertContains(page,'<button disabled>Wyrusz na wartę</button>',html=True)
        self.assertEqual(self.p.patrols.filter(track='khorinis').count(),1)
    def test_forms_render_track_costs_common_board_and_weekly_objective(self):
        self.client.force_login(self.p.user);self.region_for('khorinis')
        response=self.client.get('/warty/?track=khorinis');self.assertContains(response,'Obrona Khorinis');self.assertContains(response,'8');self.assertContains(response,'Wpisowe');self.assertContains(response,'name="track" value="khorinis"')
        self.assertContains(self.client.get('/wspolnota/'),'Tygodniowy cel wspólnoty')

class EndgamePolicyTests(SimpleTestCase):
    def test_new_policy_marks_regional_action_and_historical_policy_stays_frozen(self):
        from .bots import Observation,BaselinePolicyV23,BaselinePolicyV24
        o=Observation(100,100,False,False,None,None,None,None,True,patrol_depth=1,patrol_track='khorinis')
        self.assertEqual(BaselinePolicyV23().choose(o),('patrol',1));self.assertEqual(BaselinePolicyV24().choose(o),('regional_patrol',1))

class RegionalBuildTests(TestCase):
    def setUp(self):
        self.c,self.i,self.race=fixture();call_command('seed_khorinis',stdout=StringIO())
    def test_warrior(self):self.fight('warrior')
    def test_archer(self):self.fight('archer')
    def test_fire_mage(self):self.fight('fire')
    def test_water_mage(self):self.fight('water')
    def fight(self,build):
        from .equipment import allowed
        from .models import ItemBluePrint
        from .magic import learn_circle,purchase_magic,prepare_magic,NK_SPELLS
        from .camp_raids import rally_camp_raid,strike_camp_raid,claim_camp_raid
        from .release_probe import record_scenario
        p=person(self.c,'NEW_CAMP' if build=='water' else 'OLD_CAMP','ARCH_WATER' if build=='water' else 'ARCH_FIRE' if build=='fire' else 'BARON')
        p.level=45;p.experience=250*45*46;p.life=580;p.current_health=580;p.mana=300;p.current_mana=300;p.strength=220 if build=='warrior' else 10;p.dexterity=220 if build=='archer' else 10;p.skill_points=150;p.ore_balance=30000;p.bow_skill=60 if build=='archer' else 0;p.onehand_skill=60 if build=='warrior' else 0;p.save();succeed(self.race)
        for key in ('jark-portal','nk-sailing','nk-undead'):claimed_milestone(p,key)
        p=PlayerProfile.objects.get(pk=p.pk)
        armor=next(b for b in ItemBluePrint.objects.filter(merchant=True,kind='armor').order_by('-weapon_prot','base_value') if allowed(p,b))
        self.assertTrue(game.buy_item_from_npc(p,armor));self.assertTrue(game.equip_item(p,p.inventory.get(blueprint=armor)))
        if build in {'fire','water'}:
            for _ in range(6):self.assertTrue(learn_circle(p))
            spell=next(s for s in NK_SPELLS if s.school==build);item=purchase_magic(p,ItemBluePrint.objects.get(catalog_key=f'oe-nk-{spell.key}-rune').pk);self.assertTrue(item);self.assertTrue(prepare_magic(p,item.pk))
        else:
            for _ in range(4):self.assertTrue(game.train_attribute(p,'onehand_skill' if build=='warrior' else 'bow_skill',10))
            weapon=next(b for b in ItemBluePrint.objects.filter(merchant=True,kind='weapon',weapon_type='onehand' if build=='warrior' else 'bow',required_strength__lte=p.strength,required_dexterity__lte=p.dexterity).order_by('-damage','base_value') if allowed(p,b))
            self.assertTrue(game.buy_item_from_npc(p,weapon));self.assertTrue(game.equip_item(p,p.inventory.get(blueprint=weapon)))
            if build=='archer':self.assertTrue(game.buy_item_from_npc(p,ItemBluePrint.objects.get(catalog_key='g2nk-itrw_arrow'),100))
        now=(timezone.now()+timedelta(days=7-timezone.now().weekday())).replace(hour=12,minute=0,second=0,microsecond=0)
        with patch('django.utils.timezone.now',side_effect=lambda:now):
            for track in TRACKS:
                self.assertTrue(travel(p,self.c.pk if track=='valley' else self.i.pk))
                for depth in (1,2):
                    now+=timedelta(hours=2);game.refresh_player(p);row=patrol(p,depth,uuid4(),track);self.assertTrue(row);self.assertTrue(row.won,(build,track,row.snapshot['log']));self.assertTrue(row.snapshot['rewarded']);self.assertGreaterEqual(len(row.snapshot['loot']),2)
                    if build in {'fire','water'}:self.assertTrue(row.snapshot['magic'].startswith('nk_'));self.assertGreater(row.snapshot['casts'],0)
            raid=rally_camp_raid(p,'weekly');self.assertTrue(raid)
            for n in range(80):
                raid.refresh_from_db()
                if raid.completed_at:break
                now+=timedelta(hours=2);game.refresh_player(p);self.assertTrue(strike_camp_raid(p,raid.pk,uuid4()),(build,n,p.current_health,p.current_mana))
            self.assertIsNotNone(raid.completed_at);self.assertTrue(claim_camp_raid(p,raid.pk));self.assertEqual(p.patrols.filter(won=True).count(),8)
            self.assertTrue(all(x.unlocked==3 for x in p.regional_frontiers.all()))
        record_scenario('prepared-regional-endgame-'+build,{'synthetic_veteran_fixture':True,'ordinary_paid_gear_and_lessons':True,'grants_during_play':False,'regional_wins':8,'weekly_strikes':raid.strikes.count(),'ore_remaining':p.ore_balance,'level':p.level,'limits':['Prepared level45/attributes/ore, not organic progression.','Two-hour recovery steps, not a player-time measurement.']})

class RegionalBotTests(TestCase):
    setUp=RegionalEndgameTests.setUp
    region_for=RegionalEndgameTests.region_for
    def test_bot_executor_uses_the_same_paid_regional_patrol(self):
        from .bots import tick_bot
        self.p.is_bot=True;self.p.save();self.region_for('khorinis')
        seen=[]
        class Pick:
            def choose(self,o):seen.append(o);return 'regional_patrol',o.patrol_depth
        action,ok=tick_bot(self.p,policy=Pick(),force_active=True)
        self.assertEqual(action,'regional_patrol');self.assertTrue(ok);self.assertNotEqual(seen[0].patrol_track,'legacy');self.assertEqual(self.p.patrols.get().track,seen[0].patrol_track)
    def test_both_policy_versions_replay_their_own_saved_actions(self):
        from .bots import Observation
        from .bot_telemetry import record_decision,replay_decision
        from .models import BotDecision
        o=Observation(100,100,False,False,None,None,None,None,True,patrol_depth=1,patrol_track='khorinis')
        for version,action in [('baseline-23','patrol'),('baseline-24','regional_patrol')]:
            record_decision(self.p,o,action,1,True,policy_version=version);record=BotDecision.objects.filter(profile=self.p).first();self.assertTrue(replay_decision(record)['matches']);self.assertEqual(record.schema_version,23)
    def test_bot_executor_can_rally_and_strike_the_weekly_objective(self):
        from .bots import tick_bot
        self.p.is_bot=True;self.p.bot_turn=0;self.p.save()
        class PickRaid:
            def choose(self,o):return o.raid_action,o.raid_target
        action,ok=tick_bot(self.p,policy=PickRaid(),force_active=True);self.assertEqual(action,'raid_weekly_rally');self.assertTrue(ok)
        raid=CampRaid.objects.get(cycle='weekly');self.p.refresh_from_db();self.p.bot_turn=13;self.p.save()
        action,ok=tick_bot(self.p,policy=PickRaid(),force_active=True);self.assertEqual(action,'raid_weekly_strike');self.assertTrue(ok);self.assertEqual(raid.strikes.count(),1)

class LegacyEndgameMigrationTests(TransactionTestCase):
    def test_0052_progress_records_items_and_daily_raid_survive(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        executor=MigrationExecutor(connection);executor.migrate([('characters','0052_nk_belts')]);old=executor.loader.project_state([('characters','0052_nk_belts')]).apps
        try:
            User=old.get_model('auth','User');WorldModel=old.get_model('characters','World');Profile=old.get_model('characters','PlayerProfile');Guild=old.get_model('characters','CampGuild')
            w=WorldModel.objects.filter(is_current=True).first() or WorldModel.objects.create(name='Before endgame',is_current=True,configured=True);user=User.objects.create(username='legacy-endgame');p=Profile.objects.create(user=user,world=w,name='Legacy',ore_balance=1234)
            old.get_model('characters','FrontierProgress').objects.create(profile=p,unlocked=37,wins=90)
            record=old.get_model('characters','FrontierRecord').objects.create(profile=p,request_key=uuid4(),depth=36,won=True,points=360,season='2026-11',snapshot={'version':1,'kept':'yes'})
            guild,_=Guild.objects.get_or_create(world=w,camp='OLD_CAMP');raid=old.get_model('characters','CampRaid').objects.create(guild=guild,day=timezone.now().date(),name='Daily preserved',maximum_health=1000,health=777,attack=10,protection=5)
            bp=old.get_model('characters','ItemBluePrint').objects.create(name='Preserved blade');item=old.get_model('characters','OwnedItem').objects.create(owner=p,blueprint=bp,upgrade_level=2)
            executor=MigrationExecutor(connection);executor.migrate([('characters','0053_regional_endgame')])
            self.assertEqual(FrontierProgress.objects.get(profile_id=p.pk).unlocked,37);self.assertEqual(FrontierRecord.objects.get(pk=record.pk).snapshot,{'version':1,'kept':'yes'});self.assertEqual(FrontierRecord.objects.get(pk=record.pk).track,'legacy')
            self.assertEqual((CampRaid.objects.get(pk=raid.pk).cycle,CampRaid.objects.get(pk=raid.pk).health),('daily',777))
            from .models import OwnedItem
            self.assertEqual(OwnedItem.objects.get(pk=item.pk).upgrade_level,2);self.assertEqual(PlayerProfile.objects.get(pk=p.pk).ore_balance,1234)
        finally:MigrationExecutor(connection).migrate([('characters','0053_regional_endgame')])

class RegionalContentionTests(TransactionTestCase):
    @skipUnlessDBFeature('has_select_for_update')
    def test_two_connections_cannot_win_two_regional_rewards_in_one_cooldown(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        c,i,race=fixture();call_command('seed_khorinis',stdout=StringIO());p=person(c,'OLD_CAMP','BARON');p.level=50;p.life=2000;p.current_health=2000;p.strength=800;p.ore_balance=10000;p.save();succeed(race)
        for k in ('nk-undead','nk-sailing','jark-portal'):claimed_milestone(p,k)
        self.assertTrue(travel(p,i.pk));gate=Barrier(2)
        def worker(track):
            connections.close_all()
            try:
                actor=PlayerProfile.objects.get(pk=p.pk);gate.wait(timeout=10);return bool(patrol(actor,1,uuid4(),track))
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(worker,['khorinis','irdorath']))
        self.assertEqual(sum(results),1);self.assertEqual(FrontierRecord.objects.filter(profile=p).count(),1)
    @skipUnlessDBFeature('has_select_for_update')
    def test_weekly_claim_is_idempotent_across_two_connections(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        from .camp_raids import rally_camp_raid,strike_camp_raid,claim_camp_raid
        c,i,race=fixture();call_command('seed_khorinis',stdout=StringIO());p=person(c,'OLD_CAMP','BARON');p.level=50;p.life=2000;p.current_health=2000;p.strength=800;p.save();succeed(race);claimed_milestone(p,'nk-undead');p=PlayerProfile.objects.get(pk=p.pk)
        raid=rally_camp_raid(p,'weekly');self.assertTrue(strike_camp_raid(p,raid.pk,uuid4()));raid.health=0;raid.completed_at=timezone.now();raid.save();p.refresh_from_db();before=p.ore_balance;gate=Barrier(2)
        def worker(_):
            connections.close_all()
            try:
                actor=PlayerProfile.objects.get(pk=p.pk);gate.wait(timeout=10);return claim_camp_raid(actor,raid.pk)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:self.assertEqual(list(pool.map(worker,range(2))),[True,True])
        p.refresh_from_db();self.assertEqual(p.ore_balance,before+100);self.assertEqual(CampRaidReward.objects.filter(raid=raid).count(),1);self.assertEqual(p.inventory.get(blueprint__catalog_key='rune-dust').quantity,5)
    @skipUnlessDBFeature('has_select_for_update')
    def test_two_last_weekly_strikes_credit_guild_once(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        from .camp_raids import rally_camp_raid,strike_camp_raid
        from .barrier import guild_for
        c,i,race=fixture();call_command('seed_khorinis',stdout=StringIO());people=[]
        for _ in range(2):
            p=person(c,'OLD_CAMP','BARON');p.level=50;p.life=2000;p.current_health=2000;p.strength=800;p.save();claimed_milestone(p,'nk-undead');people.append(p)
        succeed(race);raid=rally_camp_raid(people[0],'weekly');raid.health=1;raid.save();guild=guild_for(people[0]);xp=guild.experience;gate=Barrier(2)
        def worker(pk):
            connections.close_all()
            try:
                actor=PlayerProfile.objects.get(pk=pk);gate.wait(timeout=10);return bool(strike_camp_raid(actor,raid.pk,uuid4()))
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(worker,[p.pk for p in people]))
        self.assertEqual(sum(results),1);guild.refresh_from_db();self.assertEqual(guild.experience,xp+60);self.assertEqual(raid.strikes.count(),1)
