"""World-wide chapter pools preserve event identity, timers, receipts and edits."""
from datetime import datetime,timedelta,timezone as utc
from io import StringIO
from unittest.mock import patch
from uuid import uuid4
from django.core.management import call_command
from django.db import connection
from django.test import TestCase,SimpleTestCase
from django.test.utils import CaptureQueriesContext
from .models import World,WorldEvent,WorldRelease,EventSchedule,AdventureTemplate,RegionalEventUse
from .realms import world_scope
from .world_clock import POLISH_TIME,phase_boundaries
from .world_events import ensure_world_events,reward_snapshot,active_events
from .event_narratives import STAGES,BY_STAGE,stage_for,global_text,regional_text,validate_pools
from .calendar_events import specs,seed_calendar,managed,prefix,random_spec
from .regional_events import seed_regional,managed_pattern,refresh_regional_text,context
from .test_faction_succession import fixture,person


class NarrativeCatalogTests(SimpleTestCase):
    def test_every_stage_has_full_annual_monthly_random_and_regional_pools(self):
        self.assertEqual(validate_pools(),8)
        for stage in STAGES:
            self.assertEqual(len(stage.annual),6);self.assertEqual(len(stage.monthly),12)
            self.assertEqual(len(stage.random),3);self.assertEqual(len(stage.regional),4)
            for month in range(1,13):
                title,description=global_text(stage,'monthly',month)
                self.assertIn(stage.summary,description);self.assertLessEqual(len(title),100)
        self.assertEqual(len({stage.annual for stage in STAGES}),8)
        self.assertEqual(len({stage.monthly for stage in STAGES}),8)
        self.assertEqual(len({stage.random for stage in STAGES}),8)
        for stage in STAGES[:2]:
            for text in (*stage.annual,*stage.monthly,*stage.random):
                for future in ('Irdorath','Jarkendar','smok','orkow'):
                    self.assertNotIn(future,text)

    def test_phase_requires_barrier_and_uses_highest_actual_discovery(self):
        self.assertEqual(stage_for('GOTHIC_I',{'foundations','orc-war'}).key,'colony')
        self.assertEqual(stage_for('GOTHIC_II',{'foundations'}).key,'island')
        for stage in STAGES[2:]:
            self.assertEqual(stage_for('GOTHIC_II',{'barrier',stage.key}).key,stage.key)
        self.assertEqual(stage_for('GOTHIC_I',{'barrier','night'}).key,'night')


class ChapterCalendarTests(TestCase):
    def setUp(self):
        self.c,self.i,self.race=fixture()
        World.objects.filter(pk__in=[self.c.pk,self.i.pk]).update(union_key=None)
        call_command('seed_khorinis',stdout=StringIO())
        self.p=person(self.c,'OLD_CAMP','BARON');self.p.level=50;self.p.save()
        self.now=datetime(2026,11,6,12,tzinfo=POLISH_TIME)

    def phase(self,key):
        WorldRelease.objects.all().delete()
        union=uuid4() if key not in {'colony','island'} else None
        World.objects.filter(pk__in=[self.c.pk,self.i.pk]).update(union_key=union)
        EventSchedule.objects.all().update(stamp='')
        if union:
            WorldRelease.objects.create(world=self.c,key=key,released_at=self.now,snapshot={})

    def legacy(self,spec,**overrides):
        values={k:v for k,v in spec.items() if k not in {'category','index','old'}}
        values.update(name=spec['old'][0],description=spec['old'][1]);values.update(overrides)
        return WorldEvent.objects.create(**values)

    def test_both_worlds_and_all_six_post_barrier_stages_use_their_own_pools(self):
        for stage in STAGES:
            with self.subTest(stage=stage.key):
                self.phase(stage.key)
                world=self.i if stage.key=='island' else self.c
                with world_scope(world):ensure_world_events(self.now)
                spec=next(s for s in specs(world.pk,self.now) if s['key']==prefix(world.pk)+'miners-2026')
                event=WorldEvent.objects.get(key=spec['key'])
                self.assertEqual((event.name,event.description),global_text(stage,'annual','miners'))
                self.assertEqual((event.ore_percent,event.experience_percent,event.premium_bonus),(125,110,1))
                for month in range(1,13):
                    row=WorldEvent.objects.get(key=prefix(world.pk)+f'season-window-2027-{month}')
                    self.assertEqual((row.name,row.description),global_text(stage,'monthly',month))
                for row in WorldEvent.objects.filter(world=world,region='',ends_at__gt=self.now):self.assertTrue(managed(row))

    def test_legacy_upgrade_keeps_ids_past_history_and_operator_changes(self):
        rows=specs(self.c.pk,self.now)
        live=next(s for s in rows if s['key']==prefix(self.c.pk)+'miners-2026')
        past=next(s for s in rows if s['key']==prefix(self.c.pk)+'miners-2025')
        original=self.legacy(live);history=self.legacy(past)
        before=WorldEvent.objects.filter(pk=history.pk).values().get().copy()
        with world_scope(self.c):ensure_world_events(self.now)
        original.refresh_from_db();self.assertEqual(original.name,BY_STAGE['colony'].annual[0])
        self.assertEqual(WorldEvent.objects.filter(pk=history.pk).values().get(),before)
        self.assertEqual(WorldEvent.objects.filter(key=prefix(self.c.pk)+'miners-2026').count(),1)
        for edits in ({'name':'Własne święto'}, {'description':'Własna opowieść'}, {'ore_percent':177},
                      {'ends_at':original.ends_at+timedelta(hours=1)}, {'targets':['wolf']}, {'enabled':False}):
            WorldEvent.objects.filter(pk=original.pk).update(**{k:v for k,v in live.items() if k not in {'key','category','index','old'}},name=live['old'][0],description=live['old'][1],enabled=True,targets=[])
            WorldEvent.objects.filter(pk=original.pk).update(**edits)
            old=WorldEvent.objects.filter(pk=original.pk).values().get().copy()
            seed_calendar(self.c,BY_STAGE['orc-war'],self.now)
            self.assertEqual(WorldEvent.objects.filter(pk=original.pk).values().get(),old,edits)

    def test_stage_change_mid_event_keeps_adventure_snapshot_and_economy(self):
        with patch('django.utils.timezone.now',return_value=self.now),world_scope(self.c):
            ensure_world_events()
            event=WorldEvent.objects.get(key=prefix(self.c.pk)+'miners-2026')
            fixed=(event.pk,event.starts_at,event.ends_at,event.ore_percent,event.experience_percent,event.premium_bonus)
            q=AdventureTemplate.objects.create(key='narrative-proof',name='Praca',duration_seconds=60,ore_reward=100,experience_reward=100,premium_reward=1)
            from .economy import start_adventure,claim_adventure
            run=start_adventure(self.p,q.pk)
            frozen=(run.ore_reward,run.experience_reward,run.premium_reward,run.event_names)
            self.assertIn(event.name,run.event_names)
        self.phase('dragons')
        with patch('django.utils.timezone.now',return_value=self.now+timedelta(minutes=2)),world_scope(self.c):
            ensure_world_events()
            event.refresh_from_db()
            self.assertEqual(fixed,(event.pk,event.starts_at,event.ends_at,event.ore_percent,event.experience_percent,event.premium_bonus))
            self.assertEqual(event.name,BY_STAGE['dragons'].annual[0])
            run.refresh_from_db();self.assertEqual(frozen,(run.ore_reward,run.experience_reward,run.premium_reward,run.event_names))
            self.assertTrue(claim_adventure(self.p,run.pk));self.assertFalse(claim_adventure(self.p,run.pk))

    def test_random_draw_and_dst_duration_do_not_change_with_chapter(self):
        for month,day in ((3,29),(10,25)):
            now=datetime(2026,month,day,12,tzinfo=POLISH_TIME)
            while not (spec:=random_spec(self.c.pk,now.date())):now+=timedelta(days=1)
            seed_calendar(self.c,BY_STAGE['colony'],now)
            event=WorldEvent.objects.get(key=spec['key']);fixed=(event.pk,event.starts_at,event.ends_at)
            seed_calendar(self.c,BY_STAGE['orc-war'],spec['starts_at']+timedelta(minutes=1))
            event.refresh_from_db();self.assertEqual(fixed,(event.pk,event.starts_at,event.ends_at))
            self.assertEqual(event.name,BY_STAGE['orc-war'].random[spec['index']])
            self.assertEqual(event.ends_at-event.starts_at,timedelta(hours=4))
            self.assertEqual((event.ore_percent,event.experience_percent,event.premium_bonus),(150,100,0))

    def test_merge_from_island_uses_one_canonical_schedule_and_keeps_manual_records(self):
        for world in (self.c,self.i):
            with world_scope(world):ensure_world_events(self.now)
        default=WorldEvent.objects.get(key=prefix(self.i.pk)+'miners-2026')
        manual=WorldEvent.objects.create(world=self.i,key='operator-after-join',name='Kalendarz operatora',description='Własne',starts_at=self.now-timedelta(hours=1),ends_at=self.now+timedelta(days=1),ore_percent=180)
        self.phase('barrier')
        with world_scope(self.i):ensure_world_events(self.now)
        default.refresh_from_db();manual.refresh_from_db()
        self.assertFalse(default.enabled);self.assertTrue(manual.enabled)
        self.assertEqual(default.name,BY_STAGE['island'].annual[0])
        with world_scope(self.c):
            rows=list(active_events(self.now))
            self.assertEqual(sum(e.key.endswith('miners-2026') for e in rows),1)
            self.assertIn(manual,rows)
        before=list(WorldEvent.objects.order_by('pk').values())
        with world_scope(self.i),CaptureQueriesContext(connection) as queries:ensure_world_events(self.now)
        self.assertLessEqual(len(queries),20)
        self.assertEqual(before,list(WorldEvent.objects.order_by('pk').values()))

    def test_regional_text_change_keeps_targets_rewards_timers_and_daily_use(self):
        self.now=phase_boundaries(self.now.date())[-1]+timedelta(minutes=1)
        with world_scope(self.c):ensure_world_events(self.now)
        event=WorldEvent.objects.filter(world=self.c,region='valley',starts_at__lte=self.now,ends_at__gt=self.now).first()
        self.assertIsNotNone(event);self.assertIsNotNone(managed_pattern(event))
        RegionalEventUse.objects.create(profile=self.p,event=event,request_key='already-paid',snapshot={'ore_bonus':15,'experience_bonus':30},created_at=self.now)
        fixed=(event.pk,event.starts_at,event.ends_at,event.activity,event.targets,event.ore_percent,event.experience_percent,event.art_key,event.rule_version)
        oldname=event.name
        refresh_regional_text(self.c,BY_STAGE['dragons'],self.now)
        event.refresh_from_db();self.assertNotEqual(event.name,oldname)
        self.assertEqual(fixed,(event.pk,event.starts_at,event.ends_at,event.activity,event.targets,event.ore_percent,event.experience_percent,event.art_key,event.rule_version))
        self.assertEqual(context(self.p,self.now)['uses'],2)
        event.name='Ręcznie nazwany patrol';event.save()
        old=WorldEvent.objects.filter(pk=event.pk).values().get().copy()
        refresh_regional_text(self.c,BY_STAGE['orc-war'],self.now)
        self.assertEqual(old,WorldEvent.objects.filter(pk=event.pk).values().get())

    def test_legacy_regional_text_is_adopted_without_a_new_window(self):
        from .regional_events import old_description,season_name
        with world_scope(self.c):ensure_world_events(self.now)
        event=WorldEvent.objects.filter(region='valley',ends_at__gt=self.now).first()
        title,_=managed_pattern(event)
        event.name=title;event.description=old_description(event,season_name(event.starts_at.astimezone(POLISH_TIME).date()));event.save()
        count=WorldEvent.objects.count()
        refresh_regional_text(self.c,BY_STAGE['night'],self.now)
        event.refresh_from_db();self.assertEqual(event.name,regional_text(BY_STAGE['night'],title,event.activity,'Górnicza Dolina',season_name(event.starts_at.astimezone(POLISH_TIME).date()))[0])
        self.assertEqual(WorldEvent.objects.count(),count)

    def test_calendar_get_has_plain_title_and_no_writes_or_personal_level_phase(self):
        self.phase('irdorath')
        with patch('django.utils.timezone.now',return_value=self.now),world_scope(self.c):ensure_world_events()
        self.client.force_login(self.p.user)
        before=list(WorldEvent.objects.order_by('pk').values())
        for _ in range(2):
            response=self.client.get('/wydarzenia/')
            self.assertContains(response,'Obecny etap: Żagle ku Irdorath')
            title=response.content.decode().split('<title>')[1].split('</title>')[0]
            self.assertNotIn('<section',title);self.assertLess(len(title),100)
        self.assertEqual(before,list(WorldEvent.objects.order_by('pk').values()))
        self.assertFalse(RegionalEventUse.objects.exists())

    def test_real_milestone_claim_refreshes_existing_calendar_in_the_same_action(self):
        from .models import StoryQuest
        from .story_quests import accept_story,activate_story,claim_story,choose_story
        self.phase('barrier')
        # Isolate the existing discovery hook, not the whole campaign prerequisites.
        quest=StoryQuest.objects.get(key='nk-eye')
        quest.prerequisites=[];quest.any_prerequisites=[];quest.required_choices={}
        quest.level=0;quest.objectives=[{'id':'report','kind':'talk','label':'Przekaż meldunek','options':{'report':'Zgłaszam odkrycie.'}}];quest.energy_cost=0;quest.save()
        with patch('django.utils.timezone.now',return_value=self.now),world_scope(self.c):
            ensure_world_events()
            event=WorldEvent.objects.get(key=prefix(self.c.pk)+'miners-2026')
            run=accept_story(self.p,quest.pk)
            self.assertTrue(activate_story(self.p,run.pk))
            self.assertTrue(choose_story(self.p,run.pk,'report','report'))
            self.assertTrue(claim_story(self.p,run.pk))
            event.refresh_from_db()
            self.assertEqual(event.name,BY_STAGE['dragons'].annual[0])
            self.assertTrue(WorldRelease.objects.filter(world=self.c,key='dragons').exists())

    def test_custom_regional_event_in_other_region_is_not_retired_by_merge(self):
        with world_scope(self.i):ensure_world_events(self.now)
        row=WorldEvent.objects.filter(world=self.i,region='khorinis',ends_at__gt=self.now).first()
        row.name='Portowy turniej zarządcy';row.save()
        frozen=WorldEvent.objects.filter(pk=row.pk).values().get()
        self.phase('barrier')
        with world_scope(self.i):ensure_world_events(self.now)
        self.assertEqual(frozen,WorldEvent.objects.filter(pk=row.pk).values().get())

    def test_used_slot_survives_retiring_island_window_after_merge(self):
        from .models import PlayerProfile
        now=phase_boundaries(self.now.date())[-1]+timedelta(minutes=1)
        islander=person(self.i,'CITY_WATCH','K2_COMMANDER');islander.level=50;islander.save()
        with world_scope(self.i):ensure_world_events(now)
        event=WorldEvent.objects.filter(world=self.i,region='khorinis',starts_at__lte=now,ends_at__gt=now).first()
        RegionalEventUse.objects.create(profile=islander,event=event,request_key='island-before-merge',created_at=now,snapshot={'ore_bonus':20,'experience_bonus':50})
        self.phase('barrier')
        with world_scope(self.i):ensure_world_events(now)
        event.refresh_from_db();self.assertFalse(event.enabled)
        islander=PlayerProfile.objects.get(pk=islander.pk)
        budget=context(islander,now)
        self.assertEqual((budget['uses'],budget['ore'],budget['experience']),(2,280,2950))
        self.assertEqual(RegionalEventUse.objects.filter(profile=islander).count(),1)


    def test_stale_island_scope_does_not_recreate_calendar_after_activation(self):
        from .barrier import region_ids
        with world_scope(self.i):
            self.assertEqual(region_ids(self.i),[self.i.pk])
            World.objects.filter(pk__in=[self.c.pk,self.i.pk]).update(union_key=uuid4())
            with world_scope(self.c):ensure_world_events(self.now)
            # This outer scope still cached the old, separate island.
            self.assertEqual(region_ids(self.i),[self.i.pk])
            ensure_world_events(self.now)
        self.assertFalse(WorldEvent.objects.filter(world=self.i).exists())
        self.assertTrue(WorldEvent.objects.filter(world=self.c,region='khorinis').exists())


from django.test import TransactionTestCase,skipUnlessDBFeature


@skipUnlessDBFeature('has_select_for_update')
class ChapterScheduleRaceTests(TransactionTestCase):
    def test_two_regions_initialize_one_canonical_calendar(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections,connections
        c,i,race=fixture()
        call_command('seed_khorinis',stdout=StringIO())
        now=datetime(2026,11,6,12,tzinfo=POLISH_TIME)
        gate=Barrier(2)
        def initialize(world_id):
            close_old_connections()
            try:
                gate.wait(timeout=15)
                with world_scope(world_id):ensure_world_events(now)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(initialize,[c.pk,i.pk]))
        self.assertEqual(WorldRelease.objects.filter(world=c,key='barrier').count(),1)
        self.assertEqual(WorldRelease.objects.filter(world=c,key='foundations').count(),1)
        self.assertEqual(EventSchedule.objects.filter(world=c).count(),1)
        self.assertFalse(WorldEvent.objects.filter(world=i).exists())
        self.assertEqual(WorldEvent.objects.filter(world=c,key=prefix(c.pk)+'miners-2026').count(),1)
        self.assertTrue(WorldEvent.objects.filter(world=c,region='khorinis').exists())
