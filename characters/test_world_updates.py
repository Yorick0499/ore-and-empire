"""Persistent update chapters, regional budgets, real actions and calendar boundaries."""
from datetime import datetime,timedelta,timezone as utc
from io import StringIO
from uuid import uuid4
from unittest.mock import patch
from django.test import TestCase,TransactionTestCase,skipUnlessDBFeature
from django.core.management import call_command
from django.utils import timezone
from django.db import connection
from django.test.utils import CaptureQueriesContext
from .test_faction_succession import fixture,person,succeed
from .models import WorldEvent,WorldRelease,RegionalEventUse,EventSchedule,PlayerProfile
from .world_events import ensure_world_events,reward_snapshot
from .world_releases import sync_releases,release_cards
from .world_clock import POLISH_TIME,phase_boundaries
from .realms import world_scope
from .barrier import travel
from .regional_events import context,DAILY_USES,POOLS
from . import game_logic as game

class WorldUpdateTests(TestCase):
    def setUp(self):
        self.c,self.i,self.race=fixture();call_command('seed_khorinis',stdout=StringIO())
        self.p=person(self.c,'OLD_CAMP','BARON');self.p.level=50;self.p.strength=1000;self.p.life=3000;self.p.current_health=3000;self.p.ore_balance=50000;self.p.save()
        self.now=datetime(2026,11,13,12,tzinfo=POLISH_TIME)
    def event(self,**values):
        data={'world':self.c,'key':'test-regional-'+str(uuid4()),'name':'Patrol testowy','region':'valley','activity':'hunt','targets':['wolf'],'art_key':'orc_lands','starts_at':self.now-timedelta(hours=1),'ends_at':self.now+timedelta(days=2),'ore_percent':120,'experience_percent':125}
        data.update(values);return WorldEvent.objects.create(**data)
    def reward(self,key=None,**kw):return reward_snapshot(1000,10000,profile=self.p,activity='hunt',target='wolf',consume_key=key,rates=(100,100,0,[]),**kw)
    def test_updates_follow_actual_global_and_personal_discoveries_without_grants(self):
        before=(self.p.level,self.p.ore_balance,self.p.inventory.count())
        from .models import World
        separate=World.objects.create(name='Przed Barierą',is_open=True)
        self.assertEqual(sync_releases(separate,self.now),{'foundations'})
        succeed(self.race);self.assertIn('barrier',sync_releases(self.i,self.now))
        self.assertFalse(WorldRelease.objects.filter(key='jarkendar').exists())
        from .testing_story import claimed_milestone
        for key in ('jark-portal','nk-scouts','nk-eye','nk-sailing','nk-undead'):claimed_milestone(self.p,key)
        self.assertEqual(len(sync_releases(self.i,self.now)),7);self.assertEqual(len(sync_releases(self.c,self.now)),7)
        self.assertEqual(WorldRelease.objects.filter(world=self.c).count(),7)
        self.p.refresh_from_db();self.assertEqual(before,(self.p.level,self.p.ore_balance,self.p.inventory.count()))
        row=WorldRelease.objects.get(key='jarkendar');row.snapshot['title']='Zapisana odsłona';row.save();sync_releases(self.c,self.now)
        self.assertEqual(next(r for r in release_cards(self.i) if r['key']=='jarkendar')['title'],'Zapisana odsłona')
    def test_region_cache_can_be_invalidated_in_the_activation_scope(self):
        from .models import World
        from .barrier import region_ids,clear_region_cache
        World.objects.filter(pk__in=[self.c.pk,self.i.pk]).update(union_key=None)
        with world_scope(self.c):
            self.assertEqual(region_ids(self.c),[self.c.pk])
            World.objects.filter(pk__in=[self.c.pk,self.i.pk]).update(union_key=uuid4())
            clear_region_cache();self.assertEqual(set(region_ids(self.c)),{self.c.pk,self.i.pk})
            self.assertIn('barrier',sync_releases(self.c,self.now))
    def test_regional_daily_budget_uses_polish_midnight_during_dst(self):
        for month,day in ((3,29),(10,25)):
            RegionalEventUse.objects.all().delete()
            local=datetime(2026,month,day,0,tzinfo=POLISH_TIME)
            event=self.event(starts_at=local-timedelta(hours=2),ends_at=local+timedelta(days=2))
            RegionalEventUse.objects.create(profile=self.p,event=event,request_key='dst-'+str(month),created_at=local-timedelta(seconds=1),snapshot={})
            RegionalEventUse.objects.create(profile=self.p,event=event,request_key='today-'+str(month),created_at=local+timedelta(seconds=1),snapshot={})
            self.assertEqual(context(self.p,local+timedelta(hours=12))['uses'],2)
    def test_calendar_is_stable_and_hot_seed_has_bounded_queries(self):
        with patch('django.utils.timezone.now',return_value=self.now),world_scope(self.c):
            ensure_world_events();rows=list(WorldEvent.objects.order_by('pk').values());ensure_world_events();self.assertEqual(rows,list(WorldEvent.objects.order_by('pk').values()))
            with CaptureQueriesContext(connection) as qs:ensure_world_events()
            self.assertLessEqual(len(qs),20)
        self.assertTrue(WorldEvent.objects.filter(region='valley').exists());self.assertFalse(WorldEvent.objects.filter(region='jarkendar').exists())
    def test_season_night_windows_and_dst_use_four_absolute_hours(self):
        for stamp in (datetime(2026,3,29,12,tzinfo=POLISH_TIME),datetime(2026,10,25,12,tzinfo=POLISH_TIME)):
            with world_scope(self.c):ensure_world_events(stamp)
            rows=WorldEvent.objects.filter(region='valley',starts_at__date=stamp.date())
            self.assertTrue(rows.exists())
            for row in rows:self.assertEqual((row.ends_at-row.starts_at).total_seconds(),14400)
        self.assertTrue(WorldEvent.objects.filter(key='harvest-2026').exists())
    def test_preview_and_get_never_reserve_or_pay_rewards(self):
        self.event()
        with patch('django.utils.timezone.now',return_value=self.now):
            self.assertEqual(self.reward()[:2],(1200,12500));self.assertFalse(RegionalEventUse.objects.exists())
            self.client.force_login(self.p.user);before=(self.p.ore_balance,self.p.experience,WorldRelease.objects.count())
            for _ in range(2):self.assertContains(self.client.get('/wydarzenia/'),'Aktualizacje żyjącego świata')
            self.p.refresh_from_db();self.assertEqual(before,(self.p.ore_balance,self.p.experience,WorldRelease.objects.count()));self.assertFalse(RegionalEventUse.objects.exists())
    def test_rewards_have_shared_daily_currency_and_action_caps(self):
        self.event()
        with patch('django.utils.timezone.now',return_value=self.now):
            earned=[self.reward(str(uuid4())) for _ in range(5)]
            self.assertEqual(sum(r[0]-1000 for r in earned),300);self.assertEqual(sum(r[1]-10000 for r in earned),3000)
            self.assertLessEqual(RegionalEventUse.objects.count(),3)
            for row in RegionalEventUse.objects.all():self.assertGreater(row.snapshot['ore_bonus']+row.snapshot['experience_bonus'],0)
    def test_three_small_bonuses_do_not_reset_on_travel_or_restart(self):
        self.event();succeed(self.race);self.event(region='khorinis')
        with patch('django.utils.timezone.now',return_value=self.now):
            for n in range(3):reward_snapshot(10,100,profile=self.p,activity='hunt',target='wolf',consume_key='small-'+str(n),rates=(100,100,0,[]))
            self.assertEqual(context(self.p)['uses'],0)
            self.assertTrue(travel(self.p,self.i.pk));self.p=PlayerProfile.objects.get(pk=self.p.pk)
            self.assertEqual(context(self.p)['uses'],0)
        with patch('django.utils.timezone.now',return_value=self.now+timedelta(days=1)):self.assertEqual(context(self.p)['uses'],3)
    def test_max_rule_targets_and_premium_never_stack_or_consume_useless_budget(self):
        self.event()
        with patch('django.utils.timezone.now',return_value=self.now):
            r=reward_snapshot(100,100,1,rates=(150,150,2,['Święto']),profile=self.p,activity='hunt',target='wolf',consume_key='no-gain')
            self.assertEqual(r[:3],(150,150,3));self.assertFalse(RegionalEventUse.objects.exists())
            reward_snapshot(100,100,profile=self.p,activity='hunt',target='scavenger',consume_key='wrong',rates=(100,100,0,[]));self.assertFalse(RegionalEventUse.objects.exists())
    def test_real_winning_hunt_records_bonus_once_and_rollback_keeps_everything(self):
        self.event()
        with patch('django.utils.timezone.now',return_value=self.now):
            key=uuid4();self.assertTrue(game.execute_hunt(self.p,'wolf','cavalorn',key));self.assertEqual(RegionalEventUse.objects.count(),1)
            self.assertTrue(game.execute_hunt(self.p,'wolf','cavalorn',key));self.assertEqual(RegionalEventUse.objects.count(),1)
            before=(self.p.ore_balance,self.p.experience,self.p.current_energy)
            with patch('characters.loot.save_battle',side_effect=RuntimeError('store')):
                with self.assertRaises(RuntimeError):game.execute_hunt(self.p,'wolf','cavalorn',uuid4())
            self.p.refresh_from_db();self.assertEqual(before,(self.p.ore_balance,self.p.experience,self.p.current_energy));self.assertEqual(RegionalEventUse.objects.count(),1)
    def test_jarkendar_and_irdorath_require_release_and_personal_access(self):
        succeed(self.race)
        with patch('django.utils.timezone.now',return_value=self.now),world_scope(self.c):ensure_world_events()
        self.assertFalse(WorldEvent.objects.filter(region='jarkendar').exists())
        from .testing_story import claimed_milestone
        for key in ('jark-portal','nk-sailing'):claimed_milestone(self.p,key)
        with patch('django.utils.timezone.now',return_value=self.now),world_scope(self.c):ensure_world_events()
        self.assertTrue(WorldEvent.objects.filter(region='jarkendar').exists());self.assertTrue(WorldEvent.objects.filter(region='irdorath').exists())
        self.assertFalse(WorldEvent.objects.filter(world=self.i,region='jarkendar').exists())
    def test_orc_update_adds_real_weekly_encounter_without_replacing_old_raid(self):
        succeed(self.race)
        from .testing_story import claimed_milestone
        claimed_milestone(self.p,'nk-undead');sync_releases(self.c,self.now)
        from .regional_endgame import weekly_encounter,week_start
        from .camp_raids import rally_camp_raid
        day=week_start(self.now)
        while day.toordinal()//7%5:day+=timedelta(days=7)
        with patch('django.utils.timezone.now',return_value=datetime.combine(day,datetime.min.time(),tzinfo=POLISH_TIME)+timedelta(hours=12)):
            self.assertEqual(weekly_encounter(self.c,day).key,'orc-war')
            self.assertEqual(weekly_encounter(self.c,day+timedelta(days=6)).key,'orc-war')
            raid=rally_camp_raid(self.p,'weekly');self.assertIn('Orkowie u bram',raid.name);health=raid.health
            self.assertEqual(rally_camp_raid(self.p,'weekly').pk,raid.pk);raid.refresh_from_db();self.assertEqual(raid.health,health)

class RegionalRaceTests(TransactionTestCase):
    @skipUnlessDBFeature('has_select_for_update')
    def test_two_hunts_share_one_remaining_event_slot(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        c,i,race=fixture();p=person(c,'OLD_CAMP','BARON');p.level=50;p.strength=1000;p.life=2000;p.current_health=2000;p.save()
        now=timezone.now();event=WorldEvent.objects.create(world=c,key='race-event',name='Patrol',region='valley',activity='hunt',targets=['wolf'],starts_at=now-timedelta(hours=1),ends_at=now+timedelta(hours=1),experience_percent=125)
        for n in range(2):RegionalEventUse.objects.create(profile=p,event=event,request_key='before-'+str(n),snapshot={'ore_bonus':0,'experience_bonus':1})
        gate=Barrier(2)
        def hit(n):
            connections.close_all()
            try:
                actor=PlayerProfile.objects.get(pk=p.pk);gate.wait(timeout=10);return bool(game.execute_hunt(actor,'wolf','cavalorn',uuid4()))
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:self.assertEqual(list(pool.map(hit,range(2))),[True,True])
        self.assertEqual(RegionalEventUse.objects.filter(profile=p).count(),3);self.assertEqual(p.battles.count(),2)
    @skipUnlessDBFeature('has_select_for_update')
    def test_two_worlds_record_one_shared_discovery(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        from .testing_story import claimed_milestone
        c,i,race=fixture();call_command('seed_khorinis',stdout=StringIO());p=person(c,'OLD_CAMP','BARON');claimed_milestone(p,'jark-portal')
        gate=Barrier(2)
        def discover(world):
            connections.close_all()
            try:gate.wait(timeout=10);return sync_releases(world)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            for flags in pool.map(discover,[c,i]):self.assertEqual(flags,{'foundations','barrier','jarkendar'})
        self.assertEqual(WorldRelease.objects.filter(world=c).count(),3)
        self.assertFalse(RegionalEventUse.objects.exists())
