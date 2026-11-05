from datetime import datetime,timedelta,timezone
from importlib import import_module
from django.apps import apps
from django.contrib.auth.models import User
from django.test import TestCase
from .world_clock import clock_state,phase_boundaries,POLISH_TIME,polish_day
from .challenges import period_for
from .economic_ledger import refills_remaining
from .models import WorldEvent,EnergyRefill
from .world_events import ensure_world_events

class PolishTimeTests(TestCase):
    def test_real_night_season_and_polish_date_across_utc_midnight(self):
        winter=datetime(2026,11,5,20,tzinfo=timezone.utc)
        self.assertEqual(clock_state(winter)['key'],'night')
        self.assertEqual(clock_state(datetime(2026,6,5,18,tzinfo=timezone.utc))['key'],'afternoon')
        local=datetime(2026,2,28,23,30,tzinfo=timezone.utc)
        self.assertEqual(clock_state(local)['season'],'spring')
        self.assertEqual(polish_day(local).isoformat(),'2026-03-01')
        self.assertEqual(period_for('daily',local),polish_day(local))
        self.assertEqual(period_for('weekly',datetime(2026,5,31,22,30,tzinfo=timezone.utc)).isoformat(),'2026-06-01')
    def test_dst_changes_offset_without_a_fake_phase_or_backwards_timer(self):
        for stamp,expected in [(datetime(2026,3,29,0,59,tzinfo=timezone.utc),1),(datetime(2026,3,29,1,1,tzinfo=timezone.utc),2),(datetime(2026,10,25,0,59,tzinfo=timezone.utc),2),(datetime(2026,10,25,1,1,tzinfo=timezone.utc),1)]:
            clock=clock_state(stamp)
            self.assertEqual(clock['now'].utcoffset(),timedelta(hours=expected))
            self.assertEqual(clock['key'],'night')
            self.assertGreater(clock['ends_at'].timestamp(),stamp.timestamp())
        for month in (1,6,12):
            bounds=phase_boundaries(datetime(2026,month,15).date())
            self.assertEqual(list(bounds),sorted(bounds))
            self.assertEqual(clock_state(bounds[0]-timedelta(microseconds=1))['key'],'night')
            self.assertEqual(clock_state(bounds[-1])['key'],'night')
    def test_events_use_local_midnight_and_custom_dates_survive_upgrade(self):
        ensure_world_events(datetime(2026,7,5,tzinfo=timezone.utc))
        event=WorldEvent.objects.get(key='season-window-2026-7')
        self.assertEqual(event.starts_at,datetime(2026,7,4,22,tzinfo=timezone.utc))
        old=WorldEvent.objects.create(key='miners-2040',name='Custom bonus',starts_at=datetime(2040,10,25,tzinfo=timezone.utc),ends_at=datetime(2040,11,8,tzinfo=timezone.utc),ore_percent=177)
        custom=WorldEvent.objects.create(key='winter-2040',name='Custom dates',starts_at=datetime(2040,12,19,tzinfo=timezone.utc),ends_at=datetime(2041,1,5,tzinfo=timezone.utc))
        migration=import_module('characters.migrations.0030_kalendarz_polski')
        migration.migrate_calendar(apps,None);old.refresh_from_db();custom.refresh_from_db()
        self.assertEqual(old.starts_at,datetime(2040,10,25,tzinfo=POLISH_TIME))
        self.assertEqual(old.ore_percent,177)
        self.assertEqual(custom.starts_at,datetime(2040,12,19,tzinfo=timezone.utc))
        before=old.starts_at;migration.migrate_calendar(apps,None);old.refresh_from_db();self.assertEqual(old.starts_at,before)
    def test_daily_limit_handles_23_and_25_hour_days(self):
        p=User.objects.create_user('refill-clock').playerprofile
        for month,day in ((3,29),(10,25)):
            EnergyRefill.objects.all().delete()
            start=datetime(2026,month,day,tzinfo=POLISH_TIME)
            next_day=start+timedelta(days=1)
            EnergyRefill.objects.create(profile=p,reference=f'{month}:start',created_at=start)
            EnergyRefill.objects.create(profile=p,reference=f'{month}:last',created_at=next_day.astimezone(timezone.utc)-timedelta(seconds=1))
            self.assertEqual(refills_remaining(p,next_day.astimezone(timezone.utc)-timedelta(seconds=1)),3)
            self.assertEqual(refills_remaining(p,next_day),5)
