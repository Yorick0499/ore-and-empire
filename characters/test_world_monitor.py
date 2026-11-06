from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from .models import BotDecision,BotDailySummary,OwnedItem,ItemBluePrint
from .bots import Observation,BaselinePolicyV7
from .bot_telemetry import record_decision,replay_decision
from .world_monitor import archive_decisions,world_report

class WorldMonitorTests(TestCase):
    def setUp(self):
        self.profile=User.objects.create_user('watchbot').playerprofile
        self.profile.is_bot=True;self.profile.bot_last_tick=timezone.now();self.profile.save()
    def observation(self):
        return Observation(energy=0,ore=0,busy=False,reward_ready=False,offer_id=None,inventory_id=None,blueprint_id=None,equip_id=None,armed=False,experience=0)
    def decision(self,when,**extra):
        values=dict(profile=self.profile,created_at=when,role='hunter',observation={},action='hunt',success=True,ore_delta=3,energy_delta=-15,health_delta=-2,premium_delta=1,experience_delta=20)
        values.update(extra);return BotDecision.objects.create(**values)
    def test_record_replay_and_wait_reason_are_read_only_and_versioned(self):
        observation=self.observation();self.profile.experience=12;self.profile.save()
        record_decision(self.profile,observation,'wait',None,True)
        fact=BotDecision.objects.get()
        self.assertEqual((fact.experience_delta,fact.reason,fact.policy_version),(12,'energy_recovery','baseline-15'))
        before=self.profile.current_energy
        self.assertTrue(replay_decision(fact)['matches'])
        self.profile.refresh_from_db();self.assertEqual(before,self.profile.current_energy)
        fact.policy_version='external-unknown';self.assertFalse(replay_decision(fact)['supported'])
    def test_archive_preserves_window_totals_and_raw_facts_idempotently(self):
        now=timezone.now();old=now-timedelta(days=5)
        self.decision(old);self.decision(old,success=False);self.decision(now)
        before=world_report(7,now)['totals']
        with TemporaryDirectory() as directory:
            result=archive_decisions(directory,2,now)
            self.assertEqual(result['archived'],2);self.assertEqual(Path(result['path']).stat().st_mode&0o777,0o600)
            import gzip,json
            with gzip.open(result['path'],'rt') as stream:records=[json.loads(row) for row in stream]
            self.assertEqual(len(records),2);self.assertEqual(records[0]['export_schema'],1)
            self.assertEqual(BotDailySummary.objects.get().decisions,2)
            self.assertEqual(archive_decisions(directory,2,now)['archived'],0)
            self.assertEqual(world_report(7,now)['totals'],before)
    def test_failed_archive_rolls_back_and_keeps_raw_history(self):
        self.decision(timezone.now()-timedelta(days=5))
        with TemporaryDirectory() as directory,patch.object(BotDailySummary,'save',side_effect=RuntimeError('disk/db failure')):
            with self.assertRaises(RuntimeError):archive_decisions(directory,2)
            self.assertEqual(BotDecision.objects.count(),1);self.assertFalse(BotDailySummary.objects.exists())
            self.assertEqual(list(Path(directory).iterdir()),[])
    def test_report_permissions_offer_age_and_bounded_queries_with_long_history(self):
        now=timezone.now()
        self.decision(now,action='wait',reason='energy_recovery')
        item=ItemBluePrint.objects.create(name='Ore')
        OwnedItem.objects.create(blueprint=item,owner=self.profile,is_market_listed=True,market_price=8,listed_at=now-timedelta(days=8))
        old=BotDecision.objects.first()
        old.pk=None
        BotDecision.objects.bulk_create([BotDecision(profile=self.profile,created_at=now-timedelta(days=40),role='miner',observation={},action='mine',success=True,ore_delta=0,energy_delta=-10) for _ in range(2000)])
        with CaptureQueriesContext(connection) as queries:report=world_report(7,now)
        self.assertLessEqual(len(queries),16)
        self.assertEqual(report['totals']['decisions'],1);self.assertEqual(report['states']['resting'],1)
        self.assertEqual(report['offers']['stale_7d'],1)
        self.client.force_login(self.profile.user)
        self.assertEqual(self.client.get('/zarzadca/swiat/').status_code,403)
        self.profile.user.is_superuser=True;self.profile.user.save()
        self.assertContains(self.client.get('/zarzadca/swiat/'),'Raport świata')
        export=self.client.get('/zarzadca/swiat/?format=json&days=7')
        self.assertEqual(export.json()['schema'],1)
        self.assertNotIn('password',export.content.decode())
