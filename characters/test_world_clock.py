from datetime import datetime,timedelta,timezone as utc
from io import StringIO
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command
from .world_clock import clock_state,PHASES,phase_boundaries,POLISH_TIME
from .world_events import ensure_world_events,reward_snapshot
from .models import WorldEvent,AdventureTemplate
from .economy import start_adventure,claim_adventure

class WorldClockTests(TestCase):
    def test_boundaries_all_phases_seasons_and_restart_determinism(self):
        base=datetime(2026,1,1,tzinfo=POLISH_TIME)
        bounds=phase_boundaries(base.date())
        for i,(key,name,ore,xp,_) in enumerate(PHASES):
            when=bounds[i] if i<5 else bounds[-1]
            state=clock_state(when)
            self.assertEqual((state['key'],state['ore'],state['experience']),(key,ore,xp))
            self.assertEqual(clock_state(when),state)
            self.assertEqual(clock_state(state['ends_at']-timedelta(microseconds=1))['key'],key)
            self.assertEqual(clock_state(state['ends_at'])['key'],PHASES[(i+1)%6][0])
        for month,season in [(1,'winter'),(3,'spring'),(6,'summer'),(9,'autumn'),(12,'winter')]:
            self.assertEqual(clock_state(base.replace(month=month))['season'],season)
    def test_all_rewards_are_bounded_and_strongest_wins_without_extra_premium(self):
        base=datetime(2026,1,1,tzinfo=utc.utc)
        for now in phase_boundaries(base.date()):
            with patch('django.utils.timezone.now',return_value=now):
                ore,xp,premium,names=reward_snapshot(100,100,1)
                self.assertEqual(ore+xp,215);self.assertEqual(premium,1)
                self.assertTrue(100<=ore<=110 and 100<=xp<=110)
        WorldEvent.objects.create(key='overlap',name='Duża premia',starts_at=base,ends_at=base+timedelta(days=1),ore_percent=150,experience_percent=125,premium_bonus=1)
        with patch('django.utils.timezone.now',return_value=base):self.assertEqual(reward_snapshot(100,100,1)[:3],(150,125,2))
    def test_seasonal_schedule_is_idempotent_and_adventure_keeps_snapshot(self):
        now=datetime(2026,7,5,tzinfo=utc.utc)
        ensure_world_events(now);count=WorldEvent.objects.count();ensure_world_events(now)
        self.assertEqual(WorldEvent.objects.count(),count)
        self.assertEqual(WorldEvent.objects.filter(key__startswith='season-window-2026-').count(),12)
        p=User.objects.create_user('traveller').playerprofile
        q=AdventureTemplate.objects.create(key='clock',name='Warta',duration_seconds=60,ore_reward=100,experience_reward=100,premium_reward=1)
        with patch('django.utils.timezone.now',return_value=now):run=start_adventure(p,q.pk)
        snapshot=(run.ore_reward,run.experience_reward,run.premium_reward)
        with patch('django.utils.timezone.now',return_value=now+timedelta(hours=5)):
            self.assertTrue(claim_adventure(p,run.pk));self.assertFalse(claim_adventure(p,run.pk))
        run.refresh_from_db();self.assertEqual((run.ore_reward,run.experience_reward,run.premium_reward),snapshot)

    def test_hunt_preview_includes_current_clock_and_event_bonus(self):
        p=User.objects.create_user('preview').playerprofile
        self.client.force_login(p.user)
        response=self.client.get('/polowanie/?location=exchange')
        self.assertEqual(response.context['BESTIARY']['young_scavenger']['current_reward'],reward_snapshot(0,30)[1])
        self.assertContains(response,'Następny poziom przy')
