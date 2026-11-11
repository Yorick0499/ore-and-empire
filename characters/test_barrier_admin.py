from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError,PermissionDenied
from .test_barrier import fixture
from .models import SleeperRace,BarrierEvent
from .sleeper import rally
from .barrier_admin import projection,set_paused

class BarrierAdminTests(TestCase):
    def setUp(self):
        self.colony,self.island,self.guild,self.people=fixture()
        self.admin=User.objects.create_superuser('operator',password='synthetic-test-password')
        self.client.force_login(self.admin)
    def race(self):return SleeperRace.objects.get(pk=rally(self.people[0]).race_id)
    def test_read_only_panel_does_not_create_race_or_backup(self):
        with patch('characters.barrier_activation.fresh_snapshot') as backup:
            response=self.client.get('/zarzadca/bariera/')
        self.assertEqual(response.status_code,200);self.assertEqual(len(response.context['rows']),3)
        self.assertFalse(SleeperRace.objects.exists());backup.assert_not_called()
    def test_non_admin_and_unknown_action_cannot_mutate(self):
        race=self.race();self.client.force_login(self.people[0].user)
        self.assertEqual(self.client.get('/zarzadca/bariera/').status_code,403)
        with self.assertRaises(PermissionDenied):set_paused(self.people[0].user,race.pk,True,'racing')
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post('/zarzadca/bariera/',{'action':'win','race':race.pk}).status_code,403)
    def test_pause_retry_resume_preserve_victory_and_resources(self):
        race=self.race();before=list(self.people[0].inventory.values())
        for _ in range(2):self.client.post('/zarzadca/bariera/',{'action':'pause','race':race.pk,'expected_state':'racing'})
        race.refresh_from_db();self.assertTrue(race.paused)
        self.assertEqual(BarrierEvent.objects.filter(kind='paused').count(),1)
        self.client.post('/zarzadca/bariera/',{'action':'unpause','race':race.pk,'expected_state':'racing'})
        race.refresh_from_db();self.assertFalse(race.paused);self.assertEqual(race.state,'racing');self.assertIsNone(race.winner_id)
        self.assertEqual(list(self.people[0].inventory.values()),before)
    def test_stale_state_and_active_lease_are_rejected(self):
        race=self.race()
        with self.assertRaises(ValidationError):set_paused(self.admin,race.pk,True,'failed')
        from uuid import uuid4
        race.lease_owner=uuid4();race.lease_expires_at=timezone.now()+timedelta(minutes=5);race.save()
        with self.assertRaises(ValidationError):set_paused(self.admin,race.pk,True,'racing')
    def test_operator_can_read_during_merging_but_cannot_write(self):
        race=self.race();race.winner=self.guild;race.state='merging';race.lease_expires_at=timezone.now()+timedelta(minutes=5);race.save()
        self.assertNotIn('active_character',self.client.session)
        self.assertEqual(self.client.get('/zarzadca/bariera/').status_code,200)
        self.assertNotIn('active_character',self.client.session)
        self.assertEqual(self.client.post('/zarzadca/bariera/',{'action':'pause'}).status_code,503)
        self.client.force_login(self.people[0].user);self.assertEqual(self.client.get('/zarzadca/bariera/').status_code,503)
    def test_audit_is_bounded_and_hides_private_paths(self):
        race=self.race();race.backup_path='/private/sensitive/path';race.save()
        BarrierEvent.objects.bulk_create([BarrierEvent(race=race,kind='activation_failed') for _ in range(60)])
        response=self.client.get('/zarzadca/bariera/')
        self.assertEqual(len(response.context['events']),40);self.assertNotContains(response,'/private/sensitive')
