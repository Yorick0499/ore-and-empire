from io import StringIO
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from .bots import tick_bot
from .models import BotDecision, ItemBluePrint, MarketTrade, OwnedItem
from . import game_logic as game


class BotUpgradeTests(TestCase):
    def setUp(self):
        call_command('seed_world', stdout=StringIO())
        self.bot = User.objects.create_user('armed-hunter').playerprofile
        self.bot.is_bot = True
        self.bot.camp = 'OLD_CAMP'
        self.bot.guild = 'BARON'  # No pending promotion/training distracts the regression.
        self.bot.strength = 15
        self.bot.ore_balance = 100
        self.bot.save()
        self.rusty = ItemBluePrint.objects.get(name='Zardzewiały miecz')
        self.sword = ItemBluePrint.objects.get(name='Miecz kopacza')
        self.old = OwnedItem.objects.create(owner=self.bot, blueprint=self.rusty, is_equipped=True)

    def test_armed_hunter_buys_equips_and_sells_old_weapon_before_safe_hunt(self):
        with patch('characters.bots.game.buy_item_from_npc', wraps=game.buy_item_from_npc) as purchase:
            self.assertEqual(tick_bot(self.bot, force_active=True), ('stock', True))
            purchase.assert_called_once()
        decision = BotDecision.objects.filter(profile=self.bot).first()
        self.assertIsNotNone(decision.observation['hunt_key'])
        self.assertEqual(decision.observation['upgrade_gain'], 8)
        self.assertEqual(decision.observation['upgrade_cost'], 80)
        self.assertEqual(decision.observation['ore_reserve'], 20)
        self.assertEqual(decision.ore_delta, -80)
        self.assertEqual(tick_bot(self.bot, force_active=True), ('equip', True))
        self.assertTrue(self.bot.inventory.get(blueprint=self.sword).is_equipped)
        with patch('characters.bots.game.sell_item_from_npc', wraps=game.sell_item_from_npc) as sale:
            self.assertEqual(tick_bot(self.bot, force_active=True), ('sell', True))
            sale.assert_called_once()
        self.assertFalse(OwnedItem.objects.filter(pk=self.old.pk).exists())
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.ore_balance, 32)
        self.assertEqual(tick_bot(self.bot, force_active=True), ('mine', True))

    def test_market_upgrade_uses_real_trade_and_prefers_value_over_cheapest_price(self):
        seller = User.objects.create_user('seller').playerprofile
        marginal = ItemBluePrint.objects.create(name='Marginalny', damage=15, required_strength=10, base_value=40)
        OwnedItem.objects.create(owner=seller, blueprint=marginal, is_market_listed=True, market_price=30)
        offer = OwnedItem.objects.create(owner=seller, blueprint=self.sword, is_market_listed=True, market_price=40)
        with patch('characters.bots.game.buy_item_on_market', wraps=game.buy_item_on_market) as purchase:
            self.assertEqual(tick_bot(self.bot, force_active=True), ('buy', True))
            purchase.assert_called_once()
        offer.refresh_from_db()
        self.assertEqual(offer.owner, self.bot)
        self.assertEqual(MarketTrade.objects.get().price, 40)
        self.assertEqual(tick_bot(self.bot, force_active=True), ('equip', True))

    def test_npc_wins_over_overpriced_market_upgrade(self):
        self.bot.ore_balance = 200
        self.bot.save()
        seller = User.objects.create_user('seller').playerprofile
        OwnedItem.objects.create(owner=seller, blueprint=self.sword, is_market_listed=True, market_price=90)
        self.assertEqual(tick_bot(self.bot, force_active=True), ('stock', True))
        self.assertFalse(MarketTrade.objects.exists())

    def test_reserve_strength_and_price_per_damage_filter_even_fallback_purchases(self):
        self.old.is_protected=True;self.old.save()  # Test the reserve without the separately tested financing path.
        self.bot.ore_balance = 99  # The 80 ore sword would leave less than 20.
        self.bot.save()
        self.assertNotIn(tick_bot(self.bot, force_active=True)[0], ('stock', 'buy'))
        self.assertFalse(self.bot.inventory.filter(blueprint=self.sword).exists())
        self.bot.ore_balance = 10000
        self.bot.current_energy = 0
        self.bot.save()
        self.sword.base_value = 1000  # 125 ore per additional damage is too expensive.
        self.sword.save()
        ItemBluePrint.objects.create(name='Za mały przyrost', damage=13, base_value=1, required_strength=10)
        self.assertNotIn(tick_bot(self.bot, force_active=True)[0], ('stock', 'buy'))
        self.assertEqual(self.bot.inventory.count(), 1)

    def test_full_backpack_frees_obsolete_item_then_upgrades_without_exceeding_cap(self):
        OwnedItem.objects.bulk_create([OwnedItem(owner=self.bot, blueprint=self.rusty) for _ in range(5)])
        self.assertNotIn(tick_bot(self.bot, force_active=True)[0], ('stock', 'buy'))
        self.assertEqual(self.bot.inventory.count(), 6)
        # An actually inferior spare frees a slot; equal-damage spares are retained.
        weak = ItemBluePrint.objects.create(name='Stary kij', damage=1, base_value=2)
        spare = self.bot.inventory.filter(is_equipped=False).first()
        spare.blueprint = weak
        spare.save()
        self.assertEqual(tick_bot(self.bot, force_active=True), ('sell', True))
        self.assertEqual(self.bot.inventory.count(), 5)
        self.assertEqual(tick_bot(self.bot, force_active=True), ('stock', True))
        self.assertEqual(self.bot.inventory.count(), 6)

    def test_urgent_recovery_and_busy_activity_take_precedence(self):
        self.bot.current_health = 1
        self.bot.current_energy = 0
        self.bot.save()
        self.assertEqual(tick_bot(self.bot, force_active=True), ('wait', True))
        self.assertEqual(self.bot.inventory.count(), 1)

    def test_forged_sale_cannot_sell_another_players_item(self):
        other = User.objects.create_user('other').playerprofile
        foreign = OwnedItem.objects.create(owner=other, blueprint=self.rusty)
        class ForgedPolicy:
            def choose(self, observation):
                return 'sell', foreign.pk
        self.assertEqual(tick_bot(self.bot, ForgedPolicy(), force_active=True), ('rejected', False))
        self.assertTrue(OwnedItem.objects.filter(pk=foreign.pk, owner=other).exists())
