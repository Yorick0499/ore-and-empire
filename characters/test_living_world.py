from datetime import timedelta, datetime, timezone as dt_timezone
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4
from django.contrib.auth.models import User
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import (AdventureTemplate, AdventureRun, WorldEvent, PremiumEntry,
                     StoreProduct, StorePurchase, OwnedItem, AdminAction, PlayerProfile)
from . import game_logic as game
from .economy import start_adventure, claim_adventure, purchase_product
from .world_events import ensure_world_events
from .admin_tools import administer_player, ProfileStatsForm


class LivingWorldTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("adventurer")
        self.other = User.objects.create_user("another-adventurer")
        self.profile = self.user.playerprofile
        call_command("seed_world", stdout=StringIO())
        call_command("seed_adventures", stdout=StringIO())
        WorldEvent.objects.all().delete()
        self.quest = AdventureTemplate.objects.get(key="courier")

    def finish(self, run):
        run.ends_at = timezone.now() - timedelta(seconds=1)
        run.save(update_fields=["ends_at"])

    def test_timed_quest_gate_snapshot_ownership_and_exactly_once_reward(self):
        self.assertFalse(start_adventure(self.profile, AdventureTemplate.objects.get(key="temple").pk))
        run = start_adventure(self.profile, self.quest.pk)
        self.assertIsInstance(run, AdventureRun)
        self.assertFalse(claim_adventure(self.profile, run.pk))
        self.assertFalse(start_adventure(self.profile, self.quest.pk))
        self.assertFalse(game.start_mining(self.profile, 15))
        self.assertFalse(game.execute_hunt(self.profile, "young_scavenger"))
        self.quest.ore_reward = 99999
        self.quest.enabled = False
        self.quest.save()
        self.finish(run)
        self.assertFalse(claim_adventure(self.other.playerprofile, run.pk))
        self.assertTrue(claim_adventure(self.profile, run.pk))
        self.assertFalse(claim_adventure(self.profile, run.pk))
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.ore_balance, self.profile.experience, self.profile.premium_balance), (50+run.ore_reward, run.experience_reward, 1))
        self.assertEqual(PremiumEntry.objects.get().amount, 1)

    def test_unclaimed_mining_blocks_quest_and_unfinished_quest_blocks_boss(self):
        self.assertTrue(game.start_mining(self.profile, 1))
        self.profile.action_end_time = timezone.now() - timedelta(seconds=1)
        self.profile.save()
        self.assertFalse(start_adventure(self.profile, self.quest.pk))
        self.assertTrue(game.claim_ore_reward(self.profile))
        self.profile.level = 5
        self.profile.save()
        start_adventure(self.profile, self.quest.pk)
        self.assertFalse(game.execute_boss(self.profile, "crawler_nest"))

    def test_adventure_rewards_and_claim_roll_back_on_ledger_failure(self):
        run = start_adventure(self.profile, self.quest.pk)
        self.finish(run)
        with patch.object(PremiumEntry.objects, "create", side_effect=RuntimeError("write failed")):
            with self.assertRaises(RuntimeError):
                claim_adventure(self.profile, run.pk)
        self.profile.refresh_from_db()
        run.refresh_from_db()
        self.assertIsNone(run.claimed_at)
        self.assertEqual((self.profile.ore_balance, self.profile.experience, self.profile.premium_balance), (50, 0, 0))

    def test_resource_regeneration_uses_elapsed_time_with_caps_and_fractional_remainder(self):
        now = timezone.now()
        self.profile.current_energy = 98
        self.profile.current_health = 40
        self.profile.energy_updated_at = self.profile.health_updated_at = now - timedelta(seconds=150)
        self.profile.save()
        with patch("characters.game_logic.timezone.now", return_value=now):
            game.refresh_player(self.profile)
        self.assertEqual((self.profile.current_energy, self.profile.current_health), (100, 42))
        self.assertEqual(self.profile.health_updated_at, now - timedelta(seconds=30))
        with patch("characters.game_logic.timezone.now", return_value=now + timedelta(days=2)):
            game.refresh_player(self.profile)
        self.assertEqual((self.profile.current_energy, self.profile.current_health), (100, 50))

    def test_combat_persists_injuries_and_critically_injured_player_must_rest(self):
        self.profile.current_health = 10
        self.profile.save()
        self.assertIsNot(game.execute_hunt(self.profile, "scavenger"), False)
        self.profile.refresh_from_db()
        self.assertLess(self.profile.current_health, 10)
        energy = self.profile.current_energy
        self.assertFalse(game.execute_hunt(self.profile, "scavenger"))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.current_energy, energy)

    def test_event_boundaries_snapshot_and_strongest_nonstacking_bonuses(self):
        now = timezone.now()
        event = WorldEvent.objects.create(key="test-event", name="Feast", starts_at=now, ends_at=now + timedelta(hours=1), ore_percent=150, experience_percent=200, premium_bonus=2)
        WorldEvent.objects.create(key="overlap", name="Other", starts_at=now, ends_at=now + timedelta(hours=1), ore_percent=125, experience_percent=150, premium_bonus=1)
        with patch("characters.world_events.timezone.now", return_value=now):
            run = start_adventure(self.profile, self.quest.pk)
        self.assertEqual((run.ore_reward, run.experience_reward, run.premium_reward), (18, 160, 3))
        event.enabled = False
        event.save()
        self.finish(run)
        self.assertTrue(claim_adventure(self.profile, run.pk))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.premium_balance, 3)
        with patch("characters.world_events.timezone.now", return_value=now + timedelta(hours=1)):
            run = start_adventure(self.profile, self.quest.pk)
        from .world_events import reward_snapshot
        with patch("characters.world_events.timezone.now", return_value=now+timedelta(hours=1)):
            self.assertEqual((run.ore_reward, run.experience_reward, run.premium_reward), reward_snapshot(12,80,1)[:3])

    def test_calendar_restarts_preserve_admin_edits_and_winter_crosses_year(self):
        now = datetime(2026, 12, 25, tzinfo=dt_timezone.utc)
        ensure_world_events(now)
        count = WorldEvent.objects.count()
        event = WorldEvent.objects.get(key="winter-2026")
        self.assertEqual(event.ends_at.year, 2027)
        event.enabled = False
        event.save()
        ensure_world_events(now)
        self.assertEqual(WorldEvent.objects.count(), count)
        self.assertFalse(WorldEvent.objects.get(pk=event.pk).enabled)

    def test_shop_replay_price_source_and_resource_caps(self):
        self.profile.premium_balance = 10
        self.profile.current_energy = 95
        self.profile.save()
        product = StoreProduct.objects.get(key="rice_spirit")
        token = uuid4()
        purchase = purchase_product(self.profile, product.pk, token)
        self.assertEqual(purchase.effect, 5)
        self.assertEqual(purchase_product(self.profile, product.pk, token).pk, purchase.pk)
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.premium_balance, self.profile.current_energy), (7, 100))
        self.assertFalse(purchase_product(self.profile, product.pk, uuid4()))
        self.assertEqual(StorePurchase.objects.count(), 1)
        self.assertEqual(PremiumEntry.objects.get().amount, -3)
        self.assertFalse(purchase_product(self.profile, product.pk, "not-uuid"))

    def test_shop_weapon_gate_and_failure_rolls_back_payment_and_item(self):
        product = StoreProduct.objects.get(key="rune_sword")
        self.profile.premium_balance = 30
        self.profile.save()
        self.assertFalse(purchase_product(self.profile, product.pk, uuid4()))
        self.profile.level = 8
        self.profile.save()
        with patch.object(OwnedItem.objects, "create", side_effect=RuntimeError("write failed")):
            with self.assertRaises(RuntimeError):
                purchase_product(self.profile, product.pk, uuid4())
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.premium_balance, 30)
        self.assertFalse(StorePurchase.objects.exists())
        self.assertFalse(PremiumEntry.objects.exists())
        self.assertTrue(purchase_product(self.profile, product.pk, uuid4()))
        self.assertTrue(self.profile.inventory.filter(blueprint=product.blueprint).exists())

    def test_player_forms_ignore_reward_price_and_balance_injections(self):
        self.client.force_login(self.user)
        self.client.post(reverse("adventures_page"), {"action": "start", "template": self.quest.pk, "premium_reward": 99999})
        run = AdventureRun.objects.get(profile=self.profile)
        self.assertEqual(run.premium_reward, 1)
        self.finish(run)
        self.client.post(reverse("adventures_page"), {"action": "claim", "run": run.pk, "premium_balance": 99999})
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.premium_balance, 1)
        product = StoreProduct.objects.get(key="rice_spirit")
        self.client.post(reverse("itemshop_page"), {"product": product.pk, "price": 0, "request_key": uuid4()})
        self.assertFalse(StorePurchase.objects.exists())

    def test_new_game_views_render_and_require_authentication(self):
        for route in ("adventures_page", "itemshop_page", "rankings_page"):
            self.assertEqual(self.client.get(reverse(route)).status_code, 302)
        self.client.force_login(self.user)
        for route in ("adventures_page", "itemshop_page", "rankings_page", "events_page"):
            response = self.client.get(reverse(route))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'aria-current="page"', count=1)


class GameMasterTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("world-owner", password="local-test-password")
        self.user = User.objects.create_user("ordinary-player")
        self.profile = self.user.playerprofile
        call_command("seed_world", stdout=StringIO())

    def test_superuser_gate_cannot_be_bypassed_by_staff_or_target_parameter(self):
        url = reverse("game_master")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {"profile": self.profile.pk, "action": "premium", "amount": 100}).status_code, 403)
        self.assertFalse(administer_player(self.user, self.profile.pk, "restore", {})[0])
        self.assertFalse(AdminAction.objects.exists())

    def test_restore_gift_premium_and_audit_are_real(self):
        self.profile.current_health = self.profile.current_energy = 1
        self.profile.save()
        self.assertTrue(administer_player(self.admin, self.profile.pk, "restore", {})[0])
        self.assertTrue(administer_player(self.admin, self.profile.pk, "item", {"blueprint": 1, "quantity": 2})[0])
        self.assertTrue(administer_player(self.admin, self.profile.pk, "premium", {"amount": 7})[0])
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.current_health, self.profile.current_energy, self.profile.premium_balance), (50, 100, 7))
        self.assertEqual(self.profile.inventory.count(), 2)
        self.assertEqual(AdminAction.objects.count(), 3)
        self.assertEqual(PremiumEntry.objects.get().amount, 7)

    def test_stat_form_validation_and_audit_failure_rollback(self):
        payload = {field: getattr(self.profile, field) for field in ProfileStatsForm.Meta.fields}
        payload.update(level=8, strength=40, life=150, current_health=100)
        self.assertTrue(administer_player(self.admin, self.profile.pk, "stats", payload)[0])
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.level, self.profile.strength, self.profile.life), (8, 40, 150))
        payload.update(current_health=151)
        self.assertFalse(administer_player(self.admin, self.profile.pk, "stats", payload)[0])
        with patch.object(AdminAction.objects, "create", side_effect=RuntimeError("audit failed")):
            with self.assertRaises(RuntimeError):
                administer_player(self.admin, self.profile.pk, "premium", {"amount": 10})
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.premium_balance, 0)
        self.assertFalse(PremiumEntry.objects.exists())

    def test_admin_setup_is_explicit_private_idempotent_and_never_converts_existing_user(self):
        import json
        with TemporaryDirectory() as root, override_settings(BASE_DIR=Path(root)):
            call_command("create_game_admin", username="new-owner", stdout=StringIO())
            credentials = json.loads((Path(root) / ".admin-access.json").read_text())
            user = User.objects.get(username="new-owner")
            self.assertTrue(user.is_superuser)
            self.assertTrue(user.check_password(credentials["password"]))
            self.assertEqual((Path(root) / ".admin-access.json").stat().st_mode & 0o777, 0o600)
            call_command("create_game_admin", username="new-owner", stdout=StringIO())
            with self.assertRaises(CommandError):
                call_command("create_game_admin", username=self.user.username, stdout=StringIO())
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_superuser)

    def test_game_master_page_and_django_admin_render(self):
        self.client.force_login(self.admin)
        for url in (reverse("game_master"), reverse("admin:index"), reverse("admin:characters_playerprofile_change", args=[self.profile.pk])):
            self.assertEqual(self.client.get(url).status_code, 200)


class RankingTests(TestCase):
    def test_global_camp_filters_ties_and_operator_exclusion(self):
        entries = [("first", 2, 1500, "OLD_CAMP", False), ("second", 1, 900, "NEW_CAMP", True), ("third", 1, 900, "OLD_CAMP", False)]
        for name, level, xp, camp, bot in entries:
            user = User.objects.create_user(name)
            PlayerProfile.objects.filter(user=user).update(level=level, experience=xp, camp=camp, is_bot=bot)
        owner = User.objects.create_superuser("invisible-operator")
        PlayerProfile.objects.filter(user=owner).update(level=999, experience=99999)
        self.client.force_login(User.objects.get(username="first"))
        response = self.client.get(reverse("rankings_page"))
        self.assertEqual([p.user.username for p in response.context["page"]], ["first", "second", "third"])
        self.assertEqual(response.context["camp_ranking"][0]["experience"], 2400)
        response = self.client.get(reverse("rankings_page"), {"camp": "OLD_CAMP", "population": "humans"})
        self.assertEqual([p.user.username for p in response.context["page"]], ["first", "third"])
        self.assertEqual(self.client.get(reverse("rankings_page"), {"population": "evil"}).status_code, 404)
