from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command, CommandError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import PlayerProfile, ItemBluePrint, OwnedItem, MarketTrade
from . import game_logic as game
from .bots import tick_bot


class ColonyTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="test-password-123")
        self.bob = User.objects.create_user("bob", password="test-password-123")
        self.a = self.alice.playerprofile
        self.b = self.bob.playerprofile
        self.blueprint = ItemBluePrint.objects.create(
            name="Test sword", damage=12, base_value=20
        )
        self.item = OwnedItem.objects.create(owner=self.a, blueprint=self.blueprint)

    def login(self):
        self.client.force_login(self.alice)

    def test_profile_created_for_each_account(self):
        self.assertNotEqual(self.a.pk, self.b.pk)
        self.assertEqual(self.a.ore_balance, 50)

    def test_registration_creates_profile_and_logs_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "new-prisoner",
                "password1": "Strong-colony-pass-123",
                "password2": "Strong-colony-pass-123",
            },
        )
        self.assertRedirects(response, reverse("locations_page"))
        self.assertTrue(
            PlayerProfile.objects.filter(user__username="new-prisoner").exists()
        )
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            User.objects.get(username="new-prisoner").pk,
        )

    def test_anonymous_game_views_require_login(self):
        for name in [
            "locations_page",
            "mine_page",
            "hunt_page",
            "market_page",
            "inventory_page",
            "shop_page",
            "train_page",
        ]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 302, name)

    def test_all_authenticated_pages_render(self):
        self.login()
        for name in [
            "locations_page",
            "mine_page",
            "hunt_page",
            "market_page",
            "inventory_page",
            "shop_page",
            "train_page",
        ]:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
            self.assertContains(response, "alice")
            self.assertContains(response, reverse("logout"))

    def test_login_and_post_logout(self):
        self.assertTrue(
            self.client.login(username="alice", password="test-password-123")
        )
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("login"))

    def test_actions_use_logged_in_player(self):
        self.client.force_login(self.bob)
        self.client.post(reverse("mine_page"), {"action": "mine"})
        self.a.refresh_from_db()
        self.b.refresh_from_db()
        self.assertEqual(self.a.current_energy, 100)
        self.assertEqual(self.b.current_energy, 90)

    def test_foreign_item_cannot_be_manipulated(self):
        self.client.force_login(self.bob)
        for route, payload in [
            ("inventory_page", {"action": "equip", "item_id": self.item.pk}),
            ("shop_page", {"action": "sell", "sell_item_id": self.item.pk}),
            (
                "market_page",
                {"action": "list", "sell_item_id": self.item.pk, "item_price": 10},
            ),
        ]:
            self.assertEqual(self.client.post(reverse(route), payload).status_code, 404)
        self.item.refresh_from_db()
        self.assertEqual(self.item.owner_id, self.a.pk)

    def test_malformed_identifiers_and_price_do_not_crash(self):
        self.login()
        for value in ["invalid", "-1", "9" * 50, ""]:
            response = self.client.post(
                reverse("shop_page"), {"action": "buy", "buy_item_id": value}
            )
            self.assertEqual(response.status_code, 404)
        response = self.client.post(
            reverse("market_page"),
            {
                "action": "list",
                "sell_item_id": self.item.pk,
                "item_price": "not-a-number",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_market_listed)

    def test_market_transfers_ore_and_records_trade(self):
        self.assertTrue(game.list_item_on_market(self.a, self.item, 15))
        self.assertTrue(game.buy_item_on_market(self.b, self.item))
        self.a.refresh_from_db()
        self.b.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual((self.a.ore_balance, self.b.ore_balance), (65, 35))
        self.assertEqual(self.item.owner_id, self.b.pk)
        self.assertFalse(self.item.is_market_listed)
        trade = MarketTrade.objects.get()
        self.assertEqual(
            (trade.seller_id, trade.buyer_id, trade.price), (self.a.pk, self.b.pk, 15)
        )

    def test_stale_listing_cannot_be_bought_twice(self):
        game.list_item_on_market(self.a, self.item, 15)
        stale = OwnedItem.objects.get(pk=self.item.pk)
        game.buy_item_on_market(self.b, self.item)
        self.assertFalse(game.buy_item_on_market(self.a, stale))
        self.assertEqual(MarketTrade.objects.count(), 1)

    def test_failed_transfer_rolls_back_trade_and_balances(self):
        game.list_item_on_market(self.a, self.item, 15)
        with patch.object(OwnedItem, "save", side_effect=RuntimeError("write failed")):
            with self.assertRaises(RuntimeError):
                game.buy_item_on_market(self.b, self.item)
        self.assertFalse(MarketTrade.objects.exists())
        self.a.refresh_from_db()
        self.b.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual((self.a.ore_balance, self.b.ore_balance), (50, 50))
        self.assertEqual(self.item.owner_id, self.a.pk)

    def test_invalid_and_unaffordable_market_actions(self):
        for price in [-1, 0, "1", True, game.MAX_MARKET_PRICE + 1]:
            self.assertFalse(game.list_item_on_market(self.a, self.item, price))
        game.list_item_on_market(self.a, self.item, 100)
        self.assertFalse(game.buy_item_on_market(self.a, self.item))
        self.assertFalse(game.buy_item_on_market(self.b, self.item))
        self.assertFalse(MarketTrade.objects.exists())

    def test_equipped_item_cannot_be_sold(self):
        self.assertTrue(game.equip_item(self.a, self.item))
        self.assertFalse(game.list_item_on_market(self.a, self.item, 20))
        self.assertFalse(game.sell_item_from_npc(self.a, self.item))

    def test_trade_constraints(self):
        for price, buyer in [(0, self.b), (10, self.a)]:
            with self.assertRaises(IntegrityError), transaction.atomic():
                MarketTrade.objects.create(
                    blueprint=self.blueprint, seller=self.a, buyer=buyer, price=price
                )

    def test_energy_recovers_whole_minutes_and_preserves_remainder(self):
        now = timezone.now()
        self.a.current_energy = 10
        self.a.energy_updated_at = now - timedelta(seconds=150)
        self.a.save()
        with patch("characters.game_logic.timezone.now", return_value=now):
            game.refresh_player(self.a)
        self.assertEqual(self.a.current_energy, 12)
        self.assertEqual(self.a.energy_updated_at, now - timedelta(seconds=30))

    def test_full_energy_does_not_bank_offline_time(self):
        self.a.energy_updated_at = timezone.now() - timedelta(days=1)
        self.a.save()
        game.start_mining(self.a, 15)
        game.refresh_player(self.a)
        self.assertEqual(self.a.current_energy, 90)

    def test_mining_claim_is_single_use_and_requires_completion(self):
        self.assertTrue(game.start_mining(self.a, 15))
        self.assertFalse(game.start_mining(self.a, 15))
        self.assertFalse(game.claim_ore_reward(self.a))
        self.a.action_end_time = timezone.now() - timedelta(seconds=1)
        self.a.save()
        with patch("characters.game_logic.random.randint", return_value=20):
            self.assertTrue(game.claim_ore_reward(self.a))
        self.assertFalse(game.claim_ore_reward(self.a))
        self.assertEqual(self.a.ore_balance, 70)

    def test_unknown_hunt_and_busy_hunt_cost_no_energy(self):
        self.assertFalse(game.execute_hunt(self.a, "unknown"))
        game.start_mining(self.a, 15)
        self.assertFalse(game.execute_hunt(self.a, "young_scavenger"))
        self.assertEqual(self.a.current_energy, 90)

    def test_beginner_can_win_and_gain_experience(self):
        log = game.execute_hunt(self.a, "young_scavenger")
        self.assertIsInstance(log, list)
        self.assertEqual(self.a.experience, 30)
        self.assertEqual(self.a.current_energy, 85)

    def test_training_is_allowlisted_and_charges_once(self):
        self.a.skill_points = 1
        self.a.save()
        self.assertFalse(game.train_attribute(self.a, "ore_balance"))
        self.assertTrue(game.train_attribute(self.a, "strength"))
        self.assertFalse(game.train_attribute(self.a, "strength"))
        self.assertEqual(
            (self.a.strength, self.a.ore_balance, self.a.skill_points), (11, 40, 0)
        )

    def test_level_up_awards_all_crossed_levels(self):
        self.a.experience = 1500
        self.a.save()
        game.check_level_up(self.a)
        self.assertEqual((self.a.level, self.a.skill_points), (2, 20))

    def test_location_gates_apply_to_get_and_post(self):
        self.login()
        url = reverse("hunt_page") + "?location=fog_tower"
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(
            self.client.post(url, {"monster_key": "shadowbeast"}).status_code, 403
        )
        self.a.level = 10
        self.a.save()
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("hunt_page") + "?location=missing").status_code, 404
        )

    def test_camp_gate_and_permanent_membership(self):
        self.login()
        self.a.level = 3
        self.a.save()
        url = reverse("mine_page") + "?location=free_mine"
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.post(reverse("locations_page"), {"camp": "NEW_CAMP"})
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.post(reverse("locations_page"), {"camp": "OLD_CAMP"})
        self.a.refresh_from_db()
        self.assertEqual(self.a.camp, "NEW_CAMP")

    def test_hunt_cannot_bypass_location_monster_roster(self):
        self.login()
        self.client.post(reverse("hunt_page"), {"monster_key": "shadowbeast"})
        self.a.refresh_from_db()
        self.assertEqual(self.a.current_energy, 100)

    def test_market_monitor_is_staff_only_and_exports_facts(self):
        self.login()
        self.assertEqual(self.client.get(reverse("market_monitor")).status_code, 302)
        self.alice.is_staff = True
        self.alice.save()
        game.list_item_on_market(self.a, self.item, 15)
        game.buy_item_on_market(self.b, self.item)
        self.assertContains(self.client.get(reverse("market_monitor")), "Test sword")
        response = self.client.get(reverse("market_monitor") + "?format=csv")
        self.assertContains(response, "trade_id,timestamp_utc,blueprint_id")
        self.assertEqual(len(response.content.decode().splitlines()), 2)

    def test_seed_world_is_repeatable_and_preserves_prices(self):
        call_command("seed_world", stdout=StringIO())
        count = ItemBluePrint.objects.count()
        sword = ItemBluePrint.objects.get(name="Zardzewiały miecz")
        sword.base_value = 99
        sword.save()
        call_command("seed_world", stdout=StringIO())
        sword.refresh_from_db()
        self.assertEqual(ItemBluePrint.objects.count(), count)
        self.assertEqual(sword.base_value, 99)

    def test_bot_uses_game_services_and_no_password(self):
        call_command("run_bots", create=1, limit=1, stdout=StringIO())
        bot = PlayerProfile.objects.get(is_bot=True)
        self.assertFalse(bot.user.has_usable_password())
        self.assertEqual(bot.ore_balance, 30)
        self.assertEqual(bot.inventory.count(), 1)
        tick_bot(bot)
        self.assertTrue(bot.inventory.get().is_equipped)
        surplus = OwnedItem.objects.create(owner=bot, blueprint=self.blueprint)
        bot.ore_balance = 50
        bot.current_energy = 0
        bot.save()
        self.assertEqual(tick_bot(bot), ("list", True))
        surplus.refresh_from_db()
        self.assertTrue(surplus.is_market_listed)
        self.assertEqual(surplus.market_price, 22)

    def test_bot_policy_cannot_target_human_inventory(self):
        self.b.is_bot = True
        self.b.save()

        class BadPolicy:
            def choose(policy, observation):
                return "list", self.item.pk

        self.assertEqual(tick_bot(self.b, BadPolicy()), ("rejected", False))
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_market_listed)

    def test_bot_creation_refuses_human_username_collision(self):
        user = User.objects.create_user("colony-bot-1")
        with self.assertRaises(CommandError):
            call_command("run_bots", create=1, stdout=StringIO())
        user.playerprofile.refresh_from_db()
        self.assertFalse(user.playerprofile.is_bot)

    def test_bot_command_bounds(self):
        for options in [{"create": 21}, {"limit": 0}, {"create": -1}]:
            with self.assertRaises(CommandError):
                call_command("run_bots", stdout=StringIO(), **options)

    def test_human_cannot_be_ticked(self):
        with self.assertRaises(ValueError):
            tick_bot(self.a)

    def test_completed_mining_is_claimable_after_returning(self):
        self.login()
        game.start_mining(self.a, 15)
        self.a.action_end_time = timezone.now() - timedelta(seconds=1)
        self.a.save()
        self.assertContains(self.client.get(reverse("mine_page")), "Odbierz urobek")
        self.assertFalse(game.start_mining(self.a, 15))
        self.assertTrue(game.claim_ore_reward(self.a))

    def test_equipped_bot_hunts_and_earns_experience(self):
        self.b.is_bot = True
        self.b.save()
        OwnedItem.objects.create(
            owner=self.b, blueprint=self.blueprint, is_equipped=True
        )
        self.assertEqual(tick_bot(self.b), ("hunt", True))
        self.b.refresh_from_db()
        self.assertEqual(self.b.experience, 30)

    def test_bot_purchase_records_real_trade(self):
        self.b.is_bot = True
        self.b.save()
        game.list_item_on_market(self.a, self.item, 15)
        self.assertEqual(tick_bot(self.b), ("buy", True))
        self.assertEqual(MarketTrade.objects.get().buyer_id, self.b.pk)


class BossTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("boss-hunter")
        self.profile = self.user.playerprofile
        self.profile.level = 5
        self.profile.life = 110
        self.profile.strength = 30
        self.profile.save()
        blueprint = ItemBluePrint.objects.create(
            name="Guard sword", damage=35, required_strength=30, base_value=240
        )
        OwnedItem.objects.create(
            owner=self.profile, blueprint=blueprint, is_equipped=True
        )

    def test_victory_records_report_and_awards_server_rewards(self):
        from .models import BossAttempt

        attempt = game.execute_boss(self.profile, "crawler_nest")
        self.assertTrue(attempt.won)
        self.profile.refresh_from_db()
        self.assertEqual(
            (
                self.profile.experience,
                self.profile.ore_balance,
                self.profile.current_energy,
            ),
            (300, 110, 75),
        )
        self.assertEqual(BossAttempt.objects.count(), 1)
        self.assertIn("Nagroda: 300 PD i 60 bryłek rudy.", attempt.combat_log)

    def test_cooldown_prevents_repeat_rewards_and_costs(self):
        game.execute_boss(self.profile, "crawler_nest")
        self.assertFalse(game.execute_boss(self.profile, "crawler_nest"))
        self.profile.refresh_from_db()
        self.assertEqual(
            (self.profile.experience, self.profile.current_energy), (300, 75)
        )

    def test_cooldown_expires_at_boundary(self):
        from .models import BossAttempt

        now = timezone.now()
        BossAttempt.objects.create(
            profile=self.profile,
            boss_key="crawler_nest",
            won=False,
            created_at=now - timedelta(minutes=30),
        )
        with patch("characters.game_logic.timezone.now", return_value=now):
            self.assertIsNot(game.execute_boss(self.profile, "crawler_nest"), False)

    def test_defeat_charges_energy_without_reward_and_still_cools_down(self):
        self.profile.inventory.all().delete()
        self.profile.life = 20
        self.profile.save()
        attempt = game.execute_boss(self.profile, "crawler_nest")
        self.assertFalse(attempt.won)
        self.assertEqual((attempt.experience_reward, attempt.ore_reward), (0, 0))
        self.profile.refresh_from_db()
        self.assertEqual(
            (
                self.profile.experience,
                self.profile.ore_balance,
                self.profile.current_energy,
            ),
            (0, 50, 75),
        )
        self.assertFalse(game.execute_boss(self.profile, "crawler_nest"))

    def test_invalid_locked_and_low_energy_attempts_do_not_create_reports(self):
        from .models import BossAttempt

        self.assertFalse(game.execute_boss(self.profile, "unknown"))
        self.assertFalse(game.execute_boss(self.profile, "swamp_den"))
        self.profile.current_energy = 24
        self.profile.save()
        self.assertFalse(game.execute_boss(self.profile, "crawler_nest"))
        self.assertFalse(BossAttempt.objects.exists())

    def test_working_miner_cannot_fight_boss(self):
        self.assertTrue(game.start_mining(self.profile, 15))
        self.assertFalse(game.execute_boss(self.profile, "crawler_nest"))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.current_energy, 90)

    def test_report_and_rewards_roll_back_together(self):
        from .models import BossAttempt

        with patch.object(
            BossAttempt.objects, "create", side_effect=RuntimeError("write failed")
        ):
            with self.assertRaises(RuntimeError):
                game.execute_boss(self.profile, "crawler_nest")
        self.profile.refresh_from_db()
        self.assertEqual(
            (
                self.profile.experience,
                self.profile.ore_balance,
                self.profile.current_energy,
            ),
            (0, 50, 100),
        )

    def test_boss_view_gates_and_persists_private_report(self):
        self.client.force_login(self.user)
        url = reverse("boss_page") + "?location=crawler_nest"
        self.assertContains(self.client.get(url), "Królowa pełzaczy")
        self.assertRedirects(self.client.post(url, {"ore": 999999}), url)
        self.assertContains(self.client.get(url), "Zwycięstwo")
        other = User.objects.create_user("other-hunter")
        other.playerprofile.level = 5
        other.playerprofile.save()
        self.client.force_login(other)
        self.assertNotContains(self.client.get(url), "Ostatnia wyprawa")
        self.profile.level = 4
        self.profile.save()
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(url).status_code, 403)

    def test_anonymous_boss_requires_login(self):
        self.assertEqual(self.client.get(reverse("boss_page")).status_code, 302)
