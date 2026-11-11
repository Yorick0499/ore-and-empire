from collections import Counter
from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.db.models import Q
from django.utils import timezone
from .models import PlayerProfile, WorldEvent, PremiumEntry, StorePurchase, BotDecision
from .bots import tick_bot


class AutonomousBotTests(TestCase):
    def setUp(self):
        from .world_management import seed_clean_world
        seed_clean_world()
        call_command("run_bots", create=3, create_only=True, stdout=StringIO())
        WorldEvent.objects.all().delete()

    def test_three_roles_play_earn_rest_trade_and_buy_without_resource_grants(self):
        bots = list(PlayerProfile.objects.filter(is_bot=True).order_by("pk"))
        # Include a side-quest personality; grinders/prospectors need not take optional trips.
        bots[-1].bot_personality="adventurer";bots[-1].save(update_fields=["bot_personality"])
        now = timezone.now()
        actions = Counter()
        for step in range(480):
            with patch("django.utils.timezone.now", return_value=now + timedelta(minutes=step)):
                for bot in bots:
                    action, success = tick_bot(bot, force_active=True)
                    self.assertTrue(success, (step, bot.pk, action))
                    actions[action] += 1
        for bot in bots:
            bot.refresh_from_db()
            self.assertGreater(bot.experience, 0)
            self.assertGreater(bot.level, 0)
            self.assertNotEqual(bot.camp, "NONE")
            self.assertTrue(bot.story_runs.filter(quest__key="prologue-path",status="claimed").exists())
            self.assertTrue(bot.premium_entries.filter(amount__gt=0).exists())
            self.assertLessEqual(bot.current_energy, bot.max_energy)
            self.assertLessEqual(bot.current_health, bot.max_health)
            self.assertGreaterEqual(bot.ore_balance, 0)
            self.assertGreaterEqual(bot.premium_balance, 0)
            self.assertLessEqual(bot.inventory.exclude(blueprint__kind="quest",blueprint__tradeable=False).count(), 12)
        for action in ("mine", "claim", "hunt", "train", "adventure", "adventure_claim", "shop", "accept", "promote"):
            self.assertGreater(actions[action], 0, (action, actions))
        self.assertTrue(StorePurchase.objects.exists())
        self.assertTrue(PremiumEntry.objects.filter(amount__lt=0).exists())
        # Wszystkie odłamki pochodzą z rozliczonych działań, nigdy z nadania polityki.
        allowed=Q(reference__startswith="adventure:")|Q(reference__startswith="challenge:")|Q(reference__startswith="achievement:")|Q(reference__startswith="camp-raid:")|Q(reference__startswith="story:")
        self.assertFalse(PremiumEntry.objects.filter(amount__gt=0).exclude(allowed).exists())
        from .models import PersonalChallenge,PlayerAchievement
        for entry in PremiumEntry.objects.filter(reference__startswith="challenge:"):
            self.assertTrue(PersonalChallenge.objects.filter(pk=int(entry.reference.split(":")[1]),profile=entry.profile,claimed_at__isnull=False,premium=entry.amount).exists())
        for entry in PremiumEntry.objects.filter(reference__startswith="achievement:"):
            self.assertTrue(PlayerAchievement.objects.filter(pk=int(entry.reference.split(":")[1]),profile=entry.profile,claimed_at__isnull=False).exists())
        self.assertFalse(BotDecision.objects.filter(success=False).exists())

    def test_injured_exhausted_bot_waits_and_recovers_on_next_tick(self):
        bot = PlayerProfile.objects.filter(is_bot=True).first()
        bot.current_energy = 0
        bot.current_health = 1
        bot.save()
        now = timezone.now()
        self.assertEqual(tick_bot(bot, force_active=True), ("wait", True))
        with patch("django.utils.timezone.now", return_value=now + timedelta(minutes=10)):
            action, success = tick_bot(bot, force_active=True)
        bot.refresh_from_db()
        self.assertTrue(success)
        self.assertNotEqual(action, "wait")
        self.assertGreaterEqual(bot.current_health, 10)

    def test_policy_cannot_award_shards_or_target_arbitrary_shop_products(self):
        bot = PlayerProfile.objects.filter(is_bot=True).first()
        class ForgedPolicy:
            def choose(self, observation):
                return "shop", 999999
        self.assertEqual(tick_bot(bot, ForgedPolicy(), force_active=True), ("rejected", False))
        bot.refresh_from_db()
        self.assertEqual(bot.premium_balance, 0)
        self.assertFalse(StorePurchase.objects.exists())

    def test_scheduler_supports_bounded_rounds_without_sleeping_after_last(self):
        with patch("characters.management.commands.run_bots.tick_bot", return_value=("wait", True)) as tick, patch("characters.management.commands.run_bots.time.sleep") as sleep:
            call_command("run_bots", limit=3, rounds=2, interval=1, stdout=StringIO())
        self.assertEqual(tick.call_count, 6)
        sleep.assert_called_once_with(1)

    def test_wait_records_are_sampled_and_real_shop_effects_are_logged(self):
        bot = PlayerProfile.objects.filter(is_bot=True).first()
        bot.current_energy = 0
        bot.current_health = 1
        bot.save()
        now = timezone.now()
        self.assertEqual(tick_bot(bot, force_active=True), ("wait", True))
        with patch("django.utils.timezone.now", return_value=now + timedelta(seconds=20)):
            self.assertEqual(tick_bot(bot, force_active=True), ("wait", True))
        self.assertEqual(BotDecision.objects.filter(profile=bot).count(), 1)
        bot.refresh_from_db()
        bot.premium_balance = 2
        bot.save()
        self.assertEqual(tick_bot(bot, force_active=True), ("shop", True))
        decision = BotDecision.objects.filter(profile=bot).first()
        purchase=StorePurchase.objects.filter(profile=bot).latest("pk")
        self.assertEqual(decision.health_delta,min(purchase.product.effect,bot.max_health-1))
        self.assertEqual(decision.premium_delta,-purchase.price)

    def test_malformed_policy_targets_are_rejected_before_any_action(self):
        bot = PlayerProfile.objects.filter(is_bot=True).first()
        class BadPolicy:
            def choose(self, observation):
                return "mine", -1
        self.assertEqual(tick_bot(bot, BadPolicy(), force_active=True), ("rejected", False))
        bot.refresh_from_db()
        self.assertEqual(bot.current_energy, 100)
        self.assertIsNone(bot.action_end_time)
