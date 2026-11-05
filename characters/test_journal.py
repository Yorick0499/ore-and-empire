from datetime import timedelta
from uuid import uuid4
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import BattleRecord, AdventureTemplate, AdventureRun, JournalNotice, WorldEvent
from .journal import sync_notices
from .templatetags.local_dates import local_date

class JournalTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('W'*150,password='test-pass')
        self.profile=self.user.playerprofile
        self.client.force_login(self.user)
    def test_private_paginated_reports_and_escaped_long_names(self):
        for i in range(23):
            BattleRecord.objects.create(profile=self.profile,request_key=uuid4(),monster_key='<script>bestia</script>',location_key='forest',won=True)
        other=User.objects.create_user('other').playerprofile
        hidden=BattleRecord.objects.create(profile=other,request_key=uuid4(),monster_key='sekret',location_key='forest',won=False)
        page=self.client.get(reverse('journal_page'))
        self.assertEqual(len(page.context['page']),20)
        self.assertEqual(len(self.client.get(reverse('journal_page'),{'page':2}).context['page']),3)
        self.assertNotContains(page,'<script>bestia</script>')
        self.assertEqual(self.client.get(reverse('battle_detail',args=[hidden.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse('battle_detail',args=[BattleRecord.objects.filter(profile=self.profile).first().pk])).status_code,200)
    def test_notifications_do_not_claim_rewards_and_ack_is_private(self):
        template=AdventureTemplate.objects.create(key='notice',name='Zwiad')
        run=AdventureRun.objects.create(profile=self.profile,template=template,ends_at=timezone.now()-timedelta(seconds=1),ore_reward=10,experience_reward=20,premium_reward=1)
        WorldEvent.objects.create(world=self.profile.world,key='tomorrow',name='Dzień rudy',starts_at=timezone.now()+timedelta(hours=1),ends_at=timezone.now()+timedelta(hours=2))
        other=User.objects.create_user('other').playerprofile
        secret=JournalNotice.objects.create(profile=other,key='hidden',title='Sekret',destination='events_page')
        sync_notices(self.profile);sync_notices(self.profile)
        self.assertEqual(self.profile.notices.count(),2)
        self.client.post(reverse('journal_page'))
        self.assertFalse(self.profile.notices.filter(read_at__isnull=True).exists())
        secret.refresh_from_db();self.assertIsNone(secret.read_at)
        run.refresh_from_db();self.assertIsNone(run.claimed_at)
    def test_location_filters_server_checks_and_local_fallback(self):
        response=self.client.get(reverse('locations_page'),{'availability':'open','level':0,'activity':'mine_page','edition':self.profile.world.edition})
        self.assertTrue(response.context['cards'])
        self.assertTrue(all(c['unlocked'] and c['location'].level==0 and c['location'].route=='mine_page' for c in response.context['cards']))
        self.assertEqual(self.client.get(reverse('locations_page'),{'edition':999}).context['cards'],[])
        self.assertContains(response,'filter-access')
        self.assertIn('datetime=',str(local_date(timezone.now())))
        self.assertIn('Czas polski',str(local_date(timezone.now())))
    def test_anonymous_journal_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('journal_page')).status_code,302)
