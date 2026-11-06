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
        from .world_events import reward_snapshot
        self.assertEqual(self.a.ore_balance, 50+reward_snapshot(20,0)[0])

    def test_unknown_hunt_and_busy_hunt_cost_no_energy(self):
        self.assertFalse(game.execute_hunt(self.a, "unknown"))
        game.start_mining(self.a, 15)
        self.assertFalse(game.execute_hunt(self.a, "young_scavenger"))
        self.assertEqual(self.a.current_energy, 90)

    def test_beginner_can_win_and_gain_experience(self):
        log = game.execute_hunt(self.a, "young_scavenger")
        self.assertIsInstance(log, list)
        from .world_events import reward_snapshot
        self.assertEqual(self.a.experience, reward_snapshot(0,30)[1])
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
        self.assertEqual(surplus.market_price, 21)  # 105% aktualnej referencji zamiast dawnego 110%

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
        for options in [{"create": 101}, {"limit": 0}, {"create": -1}]:
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
        self.assertGreater(self.b.experience, 0)

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

        from .world_events import reward_snapshot
        attempt = game.execute_boss(self.profile, "crawler_nest")
        self.assertTrue(attempt.won)
        self.profile.refresh_from_db()
        self.assertEqual(
            (
                self.profile.experience,
                self.profile.ore_balance,
                self.profile.current_energy,
            ),
            (reward_snapshot(0,300)[1], 50+reward_snapshot(60,0)[0], 75),
        )
        self.assertEqual(BossAttempt.objects.count(), 1)
        self.assertIn(f"Nagroda: {reward_snapshot(0,300)[1]} PD i {reward_snapshot(60,0)[0]} bryłek rudy.", attempt.combat_log)

    def test_cooldown_prevents_repeat_rewards_and_costs(self):
        from .world_events import reward_snapshot
        game.execute_boss(self.profile, "crawler_nest")
        self.assertFalse(game.execute_boss(self.profile, "crawler_nest"))
        self.profile.refresh_from_db()
        self.assertEqual(
            (self.profile.experience, self.profile.current_energy), (reward_snapshot(0,300)[1], 75)
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
        self.profile.current_health = 20
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


class LocalWorldTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("local-bot")
        self.bot = self.user.playerprofile
        self.bot.is_bot = True
        self.bot.save()
        self.blueprint = ItemBluePrint.objects.create(
            name="Starter", base_value=20, damage=12
        )

    def test_trader_lists_stock_instead_of_equipping_it(self):
        self.bot.bot_role = "trader"
        self.bot.save()
        self.assertEqual(tick_bot(self.bot), ("stock", True))
        self.assertEqual(tick_bot(self.bot), ("list", True))
        item = self.bot.inventory.get()
        self.assertTrue(item.is_market_listed)
        self.assertFalse(item.is_equipped)

    def test_miner_preserves_ore_instead_of_buying_weapons(self):
        self.bot.bot_role = "miner"
        self.bot.save()
        self.assertEqual(tick_bot(self.bot), ("mine", True))
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.ore_balance, 50)
        self.assertFalse(self.bot.inventory.exists())
        self.assertEqual(tick_bot(self.bot), ("wait", True))
        self.bot.action_end_time = timezone.now() - timedelta(seconds=1)
        self.bot.save()
        self.assertEqual(tick_bot(self.bot), ("claim", True))
        self.bot.refresh_from_db()
        self.assertGreater(self.bot.ore_balance, 50)

    def test_hunter_spends_earned_learning_points(self):
        self.bot.skill_points = 2
        self.bot.save()
        self.assertEqual(tick_bot(self.bot), ("train", True))
        self.bot.refresh_from_db()
        self.assertEqual(
            (self.bot.strength, self.bot.skill_points, self.bot.ore_balance),
            (11, 1, 40),
        )

    def test_created_population_has_three_roles_and_preserves_existing_accounts(self):
        call_command("run_bots", create=3, limit=3, stdout=StringIO())
        roles = list(
            PlayerProfile.objects.filter(user__username__startswith="colony-bot-")
            .order_by("user__username")
            .values_list("bot_role", flat=True)
        )
        self.assertEqual(roles, ["hunter", "trader", "miner"])
        miner = PlayerProfile.objects.get(user__username="colony-bot-3")
        miner.ore_balance = 123
        miner.save()
        call_command("run_bots", create=3, limit=1, stdout=StringIO())
        miner.refresh_from_db()
        self.assertEqual(miner.ore_balance, 123)

    def test_local_server_ticks_between_requests_and_stops_cleanly(self):
        from unittest.mock import MagicMock

        server = MagicMock()
        server.__enter__.return_value = server
        server.handle_request.side_effect = [None, KeyboardInterrupt]
        with patch(
            "characters.management.commands.run_colony.make_server", return_value=server
        ), patch(
            "characters.management.commands.run_colony.call_command"
        ) as setup, patch(
            "characters.management.commands.run_colony.time.monotonic",
            return_value=6,
        ), patch(
            "characters.management.commands.run_colony.tick_bot",
            return_value=("mine", True),
        ) as tick:
            call_command("run_colony", bots=1, stdout=StringIO())
        tick.assert_called_once()
        self.assertEqual(tick.call_args.args[0].pk, self.bot.pk)
        self.assertEqual([call.args[0] for call in setup.call_args_list], ["migrate", "seed_world", "seed_equipment", "seed_catalog", "seed_crafting", "seed_adventures", "seed_story", "run_bots", "archive_bot_history"])
        server.__exit__.assert_called_once()

    def test_no_bot_mode_never_ticks(self):
        from unittest.mock import MagicMock

        server = MagicMock()
        server.__enter__.return_value = server
        server.handle_request.side_effect = [None, KeyboardInterrupt]
        with patch(
            "characters.management.commands.run_colony.make_server", return_value=server
        ), patch(
            "characters.management.commands.run_colony.call_command"
        ) as setup, patch(
            "characters.management.commands.run_colony.time.monotonic",
            return_value=6,
        ), patch(
            "characters.management.commands.run_colony.tick_bot"
        ) as tick:
            call_command("run_colony", bots=0, stdout=StringIO())
        tick.assert_not_called()
        self.assertEqual([call.args[0] for call in setup.call_args_list], ["migrate", "seed_world", "seed_equipment", "seed_catalog", "seed_crafting", "seed_adventures", "seed_story", "archive_bot_history"])

    def test_busy_port_does_not_initialize_or_modify_world(self):
        with patch(
            "characters.management.commands.run_colony.make_server",
            side_effect=OSError("busy"),
        ), patch("characters.management.commands.run_colony.call_command") as setup:
            with self.assertRaises(CommandError):
                call_command("run_colony", stdout=StringIO())
        setup.assert_not_called()

    def test_invalid_local_server_options(self):
        for options in [
            {"bots": 101},
            {"bots": -1},
            {"port": 0},
            {"interval": 0},
            {"interval": float("nan")},
        ]:
            with self.assertRaises(CommandError):
                call_command("run_colony", stdout=StringIO(), **options)

    def test_broken_bot_does_not_stop_other_bots_or_http_loop(self):
        from unittest.mock import MagicMock

        other = User.objects.create_user("other-local-bot").playerprofile
        other.is_bot = True
        other.save()
        server = MagicMock()
        server.__enter__.return_value = server
        clock=[0]
        def serve():
            clock[0]+=10
            if clock[0]>20:raise KeyboardInterrupt
        server.handle_request.side_effect=serve
        errors = StringIO()
        with patch(
            "characters.management.commands.run_colony.make_server", return_value=server
        ), patch("characters.management.commands.run_colony.call_command"), patch(
            "characters.management.commands.run_colony.time.monotonic",
            side_effect=lambda:clock[0],
        ), patch(
            "characters.management.commands.run_colony.tick_bot",
            side_effect=[ValueError("bad policy"), ("wait", True)],
        ) as tick:
            call_command("run_colony", bots=2, stdout=StringIO(), stderr=errors)
        self.assertEqual(tick.call_count, 2)
        self.assertIn("bot skipped (ValueError)", errors.getvalue())
        server.__exit__.assert_called_once()

    def test_colony_and_market_show_bot_roles(self):
        self.bot.bot_role = "trader"
        self.bot.save()
        OwnedItem.objects.create(
            owner=self.bot,
            blueprint=self.blueprint,
            is_market_listed=True,
            market_price=22,
        )
        human = User.objects.create_user("local-human")
        self.client.force_login(human)
        self.assertContains(self.client.get(reverse("locations_page")), "Kupcy: 1")
        self.assertContains(self.client.get(reverse("market_page")), "[bot · Kupiec]")

    def test_population_initialization_does_not_spend_resources(self):
        call_command("run_bots", create=3, create_only=True, stdout=StringIO())
        bots = PlayerProfile.objects.filter(user__username__startswith="colony-bot-")
        self.assertEqual(bots.count(), 3)
        for bot in bots:
            self.assertEqual((bot.ore_balance, bot.current_energy), (50, 100))
            self.assertFalse(bot.inventory.exists())


class GothicInterfaceTests(TestCase):
    def test_shared_interface_on_game_screens(self):
        user = User.objects.create_user("reader", password="test-password-123")
        self.client.force_login(user)
        for route in ("locations_page", "mine_page", "hunt_page", "inventory_page", "market_page", "shop_page", "train_page"):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertContains(response, 'id="main-content"')
                self.assertContains(response, 'aria-current="page"', count=1)
                self.assertContains(response, "characters/fonts/GothicII.ttf")
                self.assertContains(response, reverse("credits_page"))
                self.assertNotContains(response, "fonts.googleapis.com")

    def test_credits_are_public(self):
        response = self.client.get(reverse("credits_page"))
        self.assertContains(response, "Patrix9999/Gothic-2-Font")

    def test_manifest_images_render_with_local_path_and_source(self):
        import json
        from django.template import Context, Template
        manifest = {"shadowbeast": {"title": "Cieniostwór", "path": "characters/art/shadowbeast.png", "source": "https://gothic.fandom.com/pl/wiki/Cieniostwór"}}
        with patch("characters.templatetags.gothic_media.MANIFEST_PATH") as path:
            path.read_text.return_value = json.dumps(manifest)
            rendered = Template("{% load gothic_media %}{% gothic_art 'shadowbeast' %}").render(Context())
        self.assertIn('/static/characters/art/shadowbeast.png', rendered)
        self.assertIn('Cieniostwór · Gothicpedia', rendered)
        self.assertIn('loading="lazy"', rendered)

    def test_failed_import_preserves_existing_assets(self):
        from characters.gothic_assets import MANIFEST_PATH
        before = MANIFEST_PATH.read_bytes()
        with patch("characters.management.commands.import_gothicpedia.read_remote", side_effect=OSError("blocked")):
            with self.assertRaisesMessage(CommandError, "no assets changed"):
                call_command("import_gothicpedia", only=["shadowbeast"])
        self.assertEqual(MANIFEST_PATH.read_bytes(), before)

    def test_successful_import_records_attribution(self):
        import json
        from pathlib import Path
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "characters/art").mkdir(parents=True)
            manifest = root / "characters/gothicpedia.json"
            manifest.write_text("{}")
            from PIL import Image
            import io
            buffer = io.BytesIO()
            Image.new('RGB',(16,16)).save(buffer,format='PNG')
            image_bytes = buffer.getvalue()
            responses = [(b'{"query":{"pages":{"1":{"imageinfo":[{"url":"https://static.wikia.nocookie.net/gothic/shadow.png"}]}}}}', "application/json"), (image_bytes, "image/png")]
            with patch("characters.management.commands.import_gothicpedia.MANIFEST_PATH", manifest), patch("characters.management.commands.import_gothicpedia.ASSET_ROOT", root / "characters"), patch("characters.management.commands.import_gothicpedia.read_remote", side_effect=responses):
                call_command("import_gothicpedia", only=["shadowbeast"], stdout=StringIO())
            asset = json.loads(manifest.read_text())["shadowbeast"]
            self.assertEqual(asset["title"], "Cieniostwór")
            self.assertIn("gothic.fandom.com/pl/wiki/", asset["source"])
            self.assertEqual((root / asset["path"]).read_bytes(), image_bytes)


class BotTelemetryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("telemetry-bot")
        self.bot = self.user.playerprofile
        self.bot.is_bot = True
        self.bot.bot_role = "miner"
        self.bot.save()

    def test_records_observation_and_actual_cost_once(self):
        from .models import BotDecision

        self.assertEqual(tick_bot(self.bot), ("mine", True))
        decision = BotDecision.objects.get()
        self.assertEqual(decision.observation["energy"], 100)
        self.assertEqual(decision.observation["role"], "miner")
        self.assertEqual((decision.action, decision.energy_delta, decision.ore_delta),
                         ("mine", -10, 0))
        self.assertEqual(decision.schema_version, 15)

    def test_rejected_target_is_recorded_without_mutation(self):
        from .models import BotDecision

        class InvalidPolicy:
            def choose(self, observation):
                return "buy", 999999

        self.assertEqual(tick_bot(self.bot, InvalidPolicy()), ("rejected", False))
        decision = BotDecision.objects.get()
        self.assertFalse(decision.success)
        self.assertIsNone(decision.target_id)
        self.assertEqual((decision.ore_delta, decision.energy_delta), (0, 0))

    def test_telemetry_failure_rolls_back_action(self):
        with patch("characters.bots.record_decision", side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                tick_bot(self.bot)
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.current_energy, 100)
        self.assertIsNone(self.bot.action_end_time)

    def test_staff_export_has_observation_and_excludes_usernames(self):
        tick_bot(self.bot)
        self.client.force_login(self.user)
        url = reverse("market_monitor") + "?format=bots-csv"
        self.assertEqual(self.client.get(url).status_code, 302)
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(url)
        self.assertContains(response, "observation_json")
        self.assertContains(response, "miner")
        self.assertNotContains(response, self.user.username)
        self.assertContains(self.client.get(reverse("market_monitor")), "Decyzje botów")
