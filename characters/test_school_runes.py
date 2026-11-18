from io import StringIO
from math import ceil

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from .bestiary import BESTIARY
from .game_logic import simulate_combat
from .magic import (
    BY_CODE, MagicPlan, bot_magic_plan, combat_plan, learn_circle, offers,
    prepare_magic, purchase_magic,
)
from .models import ItemBluePrint
from .world_management import seed_clean_world


class SchoolRuneTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_clean_world()

    def student(self, school, guild):
        profile = User.objects.create_user(school).playerprofile
        profile.camp = 'OLD_CAMP' if school == 'fire' else 'SWAMP_CAMP'
        profile.guild = guild
        profile.level = 30
        profile.skill_points = 150
        profile.ore_balance = 10000
        profile.mana = profile.current_mana = 100
        profile.life = profile.current_health = 500
        profile.save()
        return profile

    def test_paid_rune_at_each_circle_without_skipping_rank_or_school(self):
        schools = {
            'fire': ('SHADOW', 'FIRE_MAGE', 'ARCH_FIRE'),
            'brotherhood': ('NOVICE', 'GURU', 'ARCH_GURU'),
        }
        for school, ranks in schools.items():
            profile = self.student(school, ranks[0])
            for circle in range(1, 7):
                with self.subTest(school=school, circle=circle):
                    if circle in (3, 5):
                        self.assertFalse(learn_circle(profile))
                        profile.guild = ranks[(circle - 1) // 2]
                        profile.save(update_fields=['guild'])
                    rune = next(
                        row['blueprint'] for row in offers(profile)
                        if not row['scroll'] and row['spell'].school == school
                        and row['spell'].circle == circle
                    )
                    self.assertFalse(purchase_magic(profile, rune.pk))
                    before = profile.ore_balance
                    self.assertTrue(learn_circle(profile))
                    owned = purchase_magic(profile, rune.pk)
                    self.assertTrue(owned)
                    self.assertEqual(profile.ore_balance, before - circle * 50 - rune.base_value)
                    self.assertTrue(prepare_magic(profile, owned.pk))
                    self.assertEqual(combat_plan(profile).spell.circle, circle)
            other = 'brotherhood' if school == 'fire' else 'fire'
            foreign = next(
                row['blueprint'] for row in offers(profile)
                if not row['scroll'] and row['spell'].school == other
            )
            self.assertFalse(purchase_magic(profile, foreign.pk))

    def test_fire_promotion_target_can_be_defeated_with_fourth_circle_rune(self):
        profile = self.student('fire', 'FIRE_MAGE')
        profile.magic_skill = 4
        profile.save(update_fields=['magic_skill'])
        older = MagicPlan(BY_CODE['g1-itarrunefireball'][0], 0, False, 1)
        self.assertFalse(simulate_combat(profile, 'fire_golem', magic_plan=older).won)
        action, blueprint_id = bot_magic_plan(profile, [])
        self.assertEqual(action, 'buy_magic')
        blueprint = ItemBluePrint.objects.get(pk=blueprint_id)
        self.assertEqual(blueprint.catalog_key, 'oe-fire-g1-hearthlight-rune')
        owned = purchase_magic(profile, blueprint.pk)
        self.assertTrue(prepare_magic(profile, owned.pk))
        plan = combat_plan(profile)
        result = simulate_combat(profile, 'fire_golem', magic_plan=plan)
        target = BESTIARY['fire_golem']
        self.assertTrue(result.won)
        self.assertEqual(result.spell_casts, ceil(target['life'] / (plan.spell.damage - target['magic_prot'])))
        self.assertEqual(result.remaining_mana, 100 - result.spell_casts * plan.cost)

    def test_bot_buys_affordable_rune_when_best_circle_is_out_of_budget(self):
        profile = self.student('fire', 'FIRE_MAGE')
        profile.magic_skill = 4
        profile.ore_balance = 700
        profile.save(update_fields=['magic_skill', 'ore_balance'])
        action, blueprint_id = bot_magic_plan(profile, [])
        self.assertEqual(action, 'buy_magic')
        blueprint = ItemBluePrint.objects.get(pk=blueprint_id)
        self.assertLess(BY_CODE[blueprint.catalog_key][0].circle, 4)
        self.assertTrue(purchase_magic(profile, blueprint_id))

    def test_reseed_renames_existing_runes_and_preserves_items_and_operator_edits(self):
        profile = self.student('brotherhood', 'GURU')
        profile.magic_skill = 4
        profile.save(update_fields=['magic_skill'])
        blueprint = ItemBluePrint.objects.get(catalog_key='oe-brotherhood-g1-marshresonance-rune')
        owned = purchase_magic(profile, blueprint.pk)
        self.assertTrue(prepare_magic(profile, owned.pk))
        blueprint.name = 'Rezonans bagien — runa Bractwa'
        blueprint.base_value = 1234
        blueprint.save(update_fields=['name', 'base_value'])
        custom = ItemBluePrint.objects.get(catalog_key='oe-brotherhood-g2-marshresonance-rune')
        custom.name = 'Runa ze sklepu operatora'
        custom.save(update_fields=['name'])
        count = ItemBluePrint.objects.count()
        call_command('seed_equipment', stdout=StringIO())
        blueprint.refresh_from_db()
        custom.refresh_from_db()
        owned.refresh_from_db()
        self.assertEqual(blueprint.name, 'Uścisk Śniącego — runa Bractwa')
        self.assertEqual(custom.name, 'Runa ze sklepu operatora')
        self.assertEqual(owned.blueprint_id, blueprint.pk)
        self.assertEqual(combat_plan(profile).spell.name, 'Uścisk Śniącego')
        self.client.force_login(profile.user)
        self.assertContains(self.client.get('/magia/'), 'Uścisk Śniącego')
        self.assertEqual(blueprint.base_value, 1234)
        self.assertEqual(ItemBluePrint.objects.count(), count)
        self.assertEqual(BY_CODE['g1-itarscrollfirerain'][0].damage, 100)
        self.assertEqual(BY_CODE['g1-itarscrollpyrokinesis'][0].damage, 70)
