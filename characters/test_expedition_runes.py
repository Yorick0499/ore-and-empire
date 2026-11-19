from io import StringIO
from uuid import uuid4

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from .bosses import BOSSES
from .game_logic import simulate_combat
from .magic import (BY_KEY, bot_magic_plan, combat_plan, learn_circle, prepare_magic,
                    purchase_magic, spell_damage, survival_health)
from .models import ItemBluePrint, World
from .testing_story import claimed_milestone
from .world_management import seed_clean_world
from .worlds import current_world


class ExpeditionRuneTests(TestCase):
    def setUp(self):
        seed_clean_world()
        self.colony = current_world()
        self.colony.configured = True
        self.colony.save(update_fields=['configured'])
        call_command('open_khorinis', bots=0, stdout=StringIO())
        self.island = World.objects.get(universe='GOTHIC_II', is_open=True)
        self.mage = User.objects.create_user('expedition-mage').playerprofile
        self.mage.camp = 'NEW_CAMP'
        self.mage.guild = 'ARCH_WATER'
        self.mage.level = 45
        self.mage.magic_skill = 6
        self.mage.mana = self.mage.current_mana = 300
        self.mage.life = self.mage.current_health = 800
        self.mage.ore_balance = 20000
        self.mage.save()

    def test_runes_are_unlocked_by_the_barrier_and_personal_jarkendar_portal(self):
        early = ItemBluePrint.objects.get(catalog_key='oe-nk-nk_thunderstorm-rune')
        late = ItemBluePrint.objects.get(catalog_key='oe-nk-adanos_depths-rune')
        self.assertFalse(purchase_magic(self.mage, early.pk))
        self.assertFalse(purchase_magic(self.mage, late.pk))
        World.objects.filter(pk__in=(self.colony.pk, self.island.pk)).update(union_key=uuid4())
        self.assertTrue(purchase_magic(self.mage, early.pk))
        self.assertFalse(purchase_magic(self.mage, late.pk))
        claimed_milestone(self.mage, 'jark-portal')
        self.mage = type(self.mage).objects.get(pk=self.mage.pk)
        action, target = bot_magic_plan(self.mage, list(self.mage.inventory.select_related('blueprint')), BOSSES['g2nk_dragon_undead'].monster)
        self.assertEqual((action, target), ('buy_magic', late.pk))
        upgrade = purchase_magic(self.mage, late.pk)
        self.assertTrue(prepare_magic(self.mage, upgrade.pk))
        self.assertEqual(combat_plan(self.mage).spell.circle, 6)
        self.assertFalse(learn_circle(self.mage))

    def test_frontier_ward_has_a_real_combat_cost_and_forecast_matches(self):
        World.objects.filter(pk__in=(self.colony.pk, self.island.pk)).update(union_key=uuid4())
        claimed_milestone(self.mage, 'jark-portal')
        boss = BOSSES['g2nk_dragon_undead']
        weak = ItemBluePrint.objects.get(catalog_key='oe-water-g1-chainlightning-rune')
        strong = ItemBluePrint.objects.get(catalog_key='oe-nk-adanos_depths-rune')
        self.assertEqual(spell_damage(BY_KEY['chainlightning'], boss.monster), 90)
        self.assertEqual(spell_damage(BY_KEY['adanos_depths'], boss.monster), 310)
        for blueprint, expected in ((weak, False), (strong, True)):
            rune = purchase_magic(self.mage, blueprint.pk)
            self.assertTrue(prepare_magic(self.mage, rune.pk))
            plan = combat_plan(self.mage)
            forecast = survival_health(self.mage, boss.monster, plan)
            outcome = simulate_combat(self.mage, boss.key, monster=boss.monster, magic_plan=plan)
            self.assertEqual(outcome.won, expected)
            self.assertEqual(outcome.won, forecast <= self.mage.current_health)
