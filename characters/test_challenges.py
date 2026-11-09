from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from .challenges import accept_challenge,claim_challenge,record_personal_event,claim_achievement,period_for
from .models import PersonalChallenge,CampReputation,PremiumEntry
from . import game_logic as game

class ChallengeTests(TestCase):
    def setUp(self):
        self.p=User.objects.create_user('challenger').playerprofile;self.p.camp='OLD_CAMP';self.p.save()
        self.other=User.objects.create_user('other').playerprofile
    def test_period_rotation_single_reward_and_no_foreign_claim(self):
        row=accept_challenge(self.p,'daily');self.assertFalse(accept_challenge(self.p,'daily'))
        self.assertFalse(claim_challenge(self.other,row.pk));self.assertFalse(claim_challenge(self.p,row.pk))
        for _ in range(row.required):record_personal_event(self.p,row.kind)
        self.assertTrue(claim_challenge(self.p,row.pk));self.assertFalse(claim_challenge(self.p,row.pk))
        self.p.refresh_from_db();self.assertEqual((self.p.ore_balance,self.p.premium_balance),(70,1))
        self.assertEqual(CampReputation.objects.get(profile=self.p,camp='OLD_CAMP').value,5)
        self.assertEqual(PremiumEntry.objects.filter(reference=f'challenge:{row.pk}').count(),1)
        with patch('django.utils.timezone.now',return_value=timezone.now()+timedelta(days=1)):
            self.assertTrue(accept_challenge(self.p,'daily'))
    def test_expired_goal_stops_and_ready_old_goal_can_be_claimed(self):
        row=accept_challenge(self.p,'weekly');row.progress=row.required;row.save()
        with patch('django.utils.timezone.now',return_value=timezone.now()+timedelta(days=8)):
            self.assertTrue(claim_challenge(self.p,row.pk))
        second=accept_challenge(self.p,'daily')
        with patch('django.utils.timezone.now',return_value=timezone.now()+timedelta(days=1)):record_personal_event(self.p,second.kind)
        second.refresh_from_db();self.assertEqual(second.progress,0)
    def test_achievement_is_one_time_and_reward_failure_rolls_back(self):
        for _ in range(10):record_personal_event(self.p,'mine')
        with patch('characters.economy.change_premium',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):claim_achievement(self.p,'miner')
        self.assertTrue(claim_achievement(self.p,'miner'));self.assertFalse(claim_achievement(self.p,'miner'))
        self.p.refresh_from_db();self.assertEqual(self.p.premium_balance,1)
    def test_forms_ignore_forged_progress_and_bots_share_acceptance_service(self):
        self.client.force_login(self.p.user)
        self.client.post('/wyzwania/',{'action':'accept','cadence':'daily','progress':999,'premium':999})
        self.assertEqual(PersonalChallenge.objects.get(profile=self.p).progress,0)
        self.assertContains(self.client.get('/wyzwania/'),'Wyzwania mieszkańca')
        from .bots import tick_bot
        self.other.is_bot=True;self.other.bot_turn=19;self.other.save()
        self.assertEqual(tick_bot(self.other, force_active=True),('challenge_accept',True))
        self.assertEqual(PersonalChallenge.objects.filter(profile=self.other).count(),1)
