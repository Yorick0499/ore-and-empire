from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import PlayerProfile, TavernTopic, TavernMessage, BotDecision
from .community import post_message, bot_conversation, activity_rows
from .bots import tick_bot


class CommunityTests(TestCase):
    def setUp(self):
        self.human = User.objects.create_user('Podroznik', password='test-only').playerprofile
        call_command('seed_world', stdout=StringIO())
        call_command('run_bots', create=2, create_only=True, stdout=StringIO())
        self.bot, self.other = list(PlayerProfile.objects.filter(is_bot=True).order_by('pk'))

    def test_scheduler_replies_once_to_human_with_real_fact_and_heartbeat(self):
        topic = post_message(self.human, 'Gdzie zdobyć rudę?', title='Praca w kopalni')
        self.assertEqual(topic.messages.count(), 1)
        tick_bot(self.bot)
        self.bot.refresh_from_db()
        self.assertIsNotNone(self.bot.bot_last_tick)
        answer = topic.messages.filter(author=self.bot).get()
        self.assertIsNotNone(answer.decision_id)
        self.assertIn('Starej Kopalni', answer.body)
        self.assertIn('Mój ostatni zapis', answer.body)
        tick_bot(self.other)
        bot_conversation(self.bot)
        self.assertEqual(topic.messages.count(), 2)

    def test_no_fake_fact_or_answer_while_scheduler_is_not_running(self):
        topic = post_message(self.human, 'Witajcie!', title='Przy ognisku')
        bot_conversation(self.bot)
        self.assertEqual(topic.messages.count(), 1)
        self.client.force_login(self.human.user)
        for _ in range(2):
            response = self.client.get(reverse('colony_life'))
            self.assertContains(response, 'Brak świeżego sygnału')
            self.client.get(reverse('tavern_page'), {'topic': topic.pk})
        self.assertFalse(BotDecision.objects.exists())
        self.assertEqual(topic.messages.count(), 1)

    def test_validation_cooldown_and_locked_threads(self):
        for body, title in [('', 'Temat'), ('x' * 1001, 'Temat'), ('Treść', 'ab')]:
            with self.assertRaises(ValueError):
                post_message(self.human, body, title=title)
        self.assertFalse(TavernTopic.objects.exists())
        topic = post_message(self.human, 'Treść', title='Temat')
        with self.assertRaises(ValueError):
            post_message(self.human, 'Jeszcze raz', topic_id=topic.pk)
        topic.locked = True
        topic.save()
        with patch('django.utils.timezone.now', return_value=timezone.now() + timedelta(seconds=21)):
            with self.assertRaises(ValueError):
                post_message(self.human, 'Po przerwie', topic_id=topic.pk)
        self.assertEqual(topic.messages.count(), 1)

    def test_reply_cooldown_and_recent_topics_only(self):
        now = timezone.now()
        topic = post_message(self.human, 'Hej', title='Powitanie')
        tick_bot(self.bot)
        with patch('django.utils.timezone.now', return_value=now + timedelta(seconds=30)):
            post_message(self.human, 'A co z bronią?', topic_id=topic.pk)
            bot_conversation(self.bot)
        self.assertEqual(topic.messages.count(), 3)
        with patch('django.utils.timezone.now', return_value=now + timedelta(minutes=11)):
            bot_conversation(self.bot)
        self.assertEqual(topic.messages.count(), 4)

    def test_escape_html_authentication_and_long_text(self):
        self.assertEqual(self.client.get(reverse('tavern_page')).status_code, 302)
        self.assertEqual(self.client.get(reverse('colony_life')).status_code, 302)
        self.client.force_login(self.human.user)
        response = self.client.post(reverse('tavern_page'), {'title': '<script>bad</script>', 'body': '<img src=x onerror=alert(1)>'})
        self.assertEqual(response.status_code, 302)
        page = self.client.get(response.url)
        self.assertContains(page, '&lt;img')
        self.assertNotContains(page, '<img src=x')
        self.assertContains(page, 'Gothicpedia')

    def test_feed_only_successful_public_actions_and_stale_status(self):
        tick_bot(self.bot)
        fact = BotDecision.objects.filter(profile=self.bot).first()
        self.assertTrue(activity_rows())
        fact.success = False
        fact.save()
        self.assertEqual(activity_rows(), [])
        self.client.force_login(self.human.user)
        with patch('django.utils.timezone.now', return_value=timezone.now() + timedelta(minutes=2)):
            response = self.client.get(reverse('colony_life'))
        self.assertEqual(response.context['active_count'], 0)
        self.assertNotContains(response, 'observation')

    def test_pagination_limits_and_invalid_topic(self):
        topic = post_message(self.human, 'Początek', title='Długi stół')
        TavernMessage.objects.bulk_create([TavernMessage(topic=topic, author=self.human, body='Wieści') for _ in range(35)])
        self.client.force_login(self.human.user)
        response = self.client.get(reverse('tavern_page'), {'topic': topic.pk})
        self.assertEqual(len(response.context['entries']), 30)
        self.assertEqual(self.client.get(reverse('tavern_page'), {'topic': 'nonsense'}).status_code, 404)

    def test_bots_start_bounded_conversations_from_actual_play(self):
        self.bot.bot_turn = 3
        self.bot.save()
        tick_bot(self.bot)
        topic = TavernTopic.objects.get(author=self.bot)
        self.assertIsNotNone(topic.messages.get().decision_id)
        with patch('django.utils.timezone.now', return_value=timezone.now() + timedelta(minutes=11)):
            bot_conversation(self.bot)
        self.assertEqual(TavernTopic.objects.filter(author=self.bot).count(), 1)
