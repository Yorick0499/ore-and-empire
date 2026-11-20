from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from .bot_telemetry import replay_decision
from .bots import tick_bot
from .models import BotDecision, CampQuest, ItemBluePrint, OwnedItem, StoryQuest, StoryRun, World
from .realms import world_scope
from .story_gates import requirements
from .world_management import seed_clean_world


class RankedBotProgressTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_clean_world()
        cls.colony = World.objects.get(is_current=True)
        cls.colony.configured = True
        cls.colony.save(update_fields=['configured'])
        call_command('open_khorinis', bots=0, stdout=StringIO())
        cls.island = World.objects.get(universe='GOTHIC_II')

    def resident(self, world, name, **fields):
        with world_scope(world):
            profile = User.objects.create_user(name).characters.get()
        for field, value in fields.items():
            setattr(profile, field, value)
        profile.is_bot = True
        profile.save()
        return profile

    def arm(self, resident):
        weapon = ItemBluePrint.objects.create(name='Testowy miecz', damage=40, source_game='adaptation')
        OwnedItem.objects.create(owner=resident, blueprint=weapon, is_equipped=True, equipped_slot='weapon')

    def story(self, resident, key, status):
        quest = StoryQuest.objects.get(key=key)
        return StoryRun.objects.create(profile=resident, quest=quest, status=status, snapshot={
            'key': key, 'objectives': quest.objectives, 'rewards': quest.rewards, 'energy_cost': quest.energy_cost,
        })

    def test_colony_bot_completes_scavengers_with_an_open_story(self):
        p = self.resident(self.colony, 'colony-trial', camp='OLD_CAMP', guild='DIGGER',
                          level=20, strength=85, ore_balance=200, bot_turn=3)
        self.arm(p)
        for key in requirements(p, 1):
            self.story(p, key, 'claimed')
        active = self.story(p, 'old-trust-3', 'accepted')
        trial = CampQuest.objects.create(profile=p, rank_key='SHADOW', progress={'hunt:wolf': 2})
        self.assertEqual(tick_bot(p, force_active=True), ('hunt', True))
        trial.refresh_from_db()
        active.refresh_from_db()
        self.assertEqual(trial.progress['hunt:scavenger'], 1)
        self.assertEqual(active.status, 'accepted')
        self.assertTrue(replay_decision(BotDecision.objects.filter(profile=p).first())['matches'])

    def test_island_bot_runs_last_duty_with_parallel_story(self):
        p = self.resident(self.island, 'island-trial', camp='CITY_WATCH', guild='K2_MILITIA',
                          level=20, strength=70, ore_balance=200, bot_turn=3)
        self.arm(p)
        for key in requirements(p, 2):
            self.story(p, key, 'claimed')
        self.story(p, 'k2-supply-1', 'accepted')
        trial = CampQuest.objects.create(profile=p, rank_key='K2_PALADIN', progress={
            '_trial_version': 3, 'hunt:k2_field_raider': 3, 'boss:k2_bandit_boss': 1, 'duty:route': 6,
        })
        now = timezone.now()
        self.assertEqual(tick_bot(p, force_active=True), ('adventure', True))
        with patch('django.utils.timezone.now', return_value=now + timedelta(hours=2)):
            self.assertEqual(tick_bot(p, force_active=True), ('adventure_claim', True))
            self.assertEqual(tick_bot(p, force_active=True), ('promote', True))
        trial.refresh_from_db()
        self.assertEqual(trial.progress['duty:route'], 7)
        self.assertIsNotNone(trial.promoted_at)

    def test_equipped_warrior_buys_armor_then_trains_weapon_skill(self):
        p = self.resident(self.colony, 'armor-buyer', level=5, strength=30, ore_balance=150,
                          skill_points=8, bot_turn=3)
        self.arm(p)
        self.assertEqual(tick_bot(p, force_active=True), ('armor', True))
        self.assertEqual(tick_bot(p, force_active=True), ('equip', True))
        self.assertTrue(p.inventory.filter(equipped_slot='armor', is_equipped=True).exists())
        seen = []
        class TrainPolicy:
            def choose(self, obs):
                seen.append(obs.training)
                return 'train', None
        self.assertEqual(tick_bot(p, policy=TrainPolicy(), force_active=True), ('train', True))
        p.refresh_from_db()
        self.assertEqual(seen, ['onehand_skill'])
        self.assertEqual(p.onehand_skill, 1)

    def test_spare_runes_preserve_the_cheap_strong_and_prepared_options(self):
        from .magic import spare_rune

        p = self.resident(self.colony, 'rune-owner')
        codes = ('g1-itarrunewindfist', 'oe-brotherhood-g1-marshpulse-rune',
                 'oe-brotherhood-g1-marshsilence-rune')
        runes = [OwnedItem.objects.create(owner=p, blueprint=ItemBluePrint.objects.get(catalog_key=key))
                 for key in codes]
        self.assertEqual(spare_rune(runes, runes, set()), runes[1])
        self.assertIsNone(spare_rune(runes, runes, {runes[1].pk}))

    def test_unarmed_island_adventurer_buys_ranged_weapon_and_ammo(self):
        p = self.resident(self.island, 'ranged-starter', ore_balance=100, bot_turn=2,
                          bot_role='hunter', bot_personality='adventurer')
        self.assertEqual(tick_bot(p, force_active=True), ('stock', True))
        self.assertEqual(tick_bot(p, force_active=True), ('equip', True))
        weapon = p.inventory.get(is_equipped=True, equipped_slot='weapon').blueprint
        self.assertIn(weapon.weapon_type, ('bow', 'crossbow'))
        self.assertEqual(tick_bot(p, force_active=True), ('ammo', True))
        self.assertTrue(p.inventory.filter(blueprint__kind='ammo', blueprint__original_stats__ammo_type=(
            'arrow' if weapon.weapon_type == 'bow' else 'bolt')).exists())
