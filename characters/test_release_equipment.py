from datetime import timedelta
from io import StringIO
import random
from unittest.mock import patch

from django.apps import apps
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from . import game_logic as game
from .bestiary import BESTIARY
from .bosses import BOSSES
from .equipment import add_item, compare_equipment
from .faction_succession_v2 import apply
from .magic import bot_magic_plan, combat_plan, prepare_magic, purchase_magic
from .models import ItemBluePrint, WorldRelease
from .release_equipment import GEAR, published
from .release_equipment_v1 import DELIVERIES, definitions, seed
from .release_probe import record_scenario
from .test_faction_succession import fixture, person
from .testing_story import claimed_milestone
from .world_releases import sync_releases


class ReleaseEquipmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.colony, cls.island, cls.race = fixture()
        call_command('seed_khorinis', stdout=StringIO())
        cls.mage = person(cls.colony, 'NEW_CAMP', 'ARCH_WATER')
        cls.buyer = person(cls.island, 'CITY_WATCH', 'K2_COMMANDER')
        for profile in (cls.mage, cls.buyer):
            profile.level = 60
            profile.strength = profile.dexterity = 145
            profile.magic_skill = 6
            profile.ore_balance = 20000
            profile.save()

    def announce(self, release, **fields):
        return WorldRelease.objects.create(world=self.colony, key=release, **fields)

    def blueprint(self, release, suffix):
        return ItemBluePrint.objects.get(catalog_key=f'oe-release-{release}-{suffix}')

    def test_separate_worlds_and_future_dates_cannot_unlock_stock_early(self):
        future = self.announce('barrier', released_at=timezone.now() + timedelta(days=1))
        early = self.blueprint('barrier', 'trail-bow')
        self.assertFalse(game.buy_item_from_npc(self.buyer, early))
        future.released_at = timezone.now()
        future.save(update_fields=['released_at'])
        self.assertIn('barrier', published(self.buyer.world_id))
        self.assertTrue(game.buy_item_from_npc(self.buyer, early))
        self.island.union_key = None
        self.island.save(update_fields=['union_key'])
        self.assertFalse(game.buy_item_from_npc(self.buyer, early))
        self.assertFalse(game.buy_item_from_npc(self.mage, early))

    def test_player_surfaces_and_direct_services_match_public_and_personal_gates(self):
        self.announce('barrier')
        pending = self.blueprint('jarkendar', 'trail-bow')
        master = self.blueprint('jarkendar', 'master-bow')
        item = add_item(self.buyer, pending, origin='admin')
        self.assertFalse(game.list_item_on_market(self.buyer, item, 100))
        self.assertFalse(game.equip_item(self.buyer, item))
        self.assertTrue(compare_equipment(self.buyer, item)['requirements'])
        self.assertFalse(game.buy_item_from_npc(self.buyer, pending))
        # A manually inserted offer must still be rejected by the settlement service.
        item.is_market_listed = True
        item.market_price = 100
        item.save(update_fields=['is_market_listed', 'market_price'])
        self.assertFalse(game.buy_item_on_market(self.mage, item, 100))
        self.assertTrue(game.delist_item_from_market(self.buyer, item))
        self.client.force_login(self.buyer.user)
        shop = reverse('shop_page')
        before = self.client.get(shop, {'q': pending.name})
        self.assertNotIn(pending, before.context['shop_items'])
        self.announce('jarkendar')
        response = self.client.get(shop, {'release': 'jarkendar', 'q': pending.name})
        self.assertContains(response, pending.name)
        self.assertContains(response, 'Zaginiona Dolina')
        self.assertTrue(game.list_item_on_market(self.buyer, item, 100))
        self.assertTrue(game.buy_item_on_market(self.mage, item, 100))
        self.assertFalse(game.buy_item_from_npc(self.buyer, master))
        claimed_milestone(self.buyer, 'jark-portal')
        buyer = type(self.buyer).objects.get(pk=self.buyer.pk)
        self.assertTrue(game.buy_item_from_npc(buyer, master))
        self.assertTrue(game.equip_item(buyer, buyer.inventory.get(blueprint=master)))

    def test_actual_milestone_sync_updates_scoped_equipment_availability(self):
        from .realms import world_scope

        sync_releases(self.colony)
        with world_scope(self.colony):
            self.assertEqual(published(self.colony.pk), {'barrier'})
            claimed_milestone(self.mage, 'jark-portal')
            sync_releases(self.colony)
            self.assertEqual(published(self.colony.pk), {'barrier', 'jarkendar'})
        self.assertNotIn('night', published(self.colony.pk))

    def test_magic_power_requires_release_circle_and_school_and_bots_can_select_it(self):
        rune = self.blueprint('jarkendar', 'master-water-rune')
        self.assertFalse(purchase_magic(self.mage, rune.pk))
        self.announce('jarkendar')
        self.assertFalse(purchase_magic(self.mage, rune.pk))
        claimed_milestone(self.mage, 'jark-portal')
        self.mage = type(self.mage).objects.get(pk=self.mage.pk)
        self.mage.magic_skill = 4
        self.mage.save(update_fields=['magic_skill'])
        self.assertFalse(purchase_magic(self.mage, rune.pk))
        self.assertFalse(purchase_magic(self.buyer, self.blueprint('jarkendar', 'trail-water-rune').pk))
        self.mage.magic_skill = 6
        self.mage.save(update_fields=['magic_skill'])
        self.assertEqual(bot_magic_plan(self.mage, []), ('buy_magic', rune.pk))
        purchased = purchase_magic(self.mage, rune.pk)
        self.assertTrue(prepare_magic(self.mage, purchased.pk))
        self.assertEqual(combat_plan(self.mage).spell.circle, 6)

    def test_seed_preserves_edited_items(self):
        edited = self.blueprint('night', 'trail-onehand')
        edited.name = 'Mój rynsztunek zwiadowcy'
        edited.save(update_fields=['name'])
        seed(ItemBluePrint.objects)
        edited.refresh_from_db()
        self.assertEqual(edited.name, 'Mój rynsztunek zwiadowcy')
        self.assertEqual(ItemBluePrint.objects.filter(catalog_key__in=GEAR).count(), len(GEAR))

    def test_all_release_bands_cover_supported_builds_and_power_increases(self):
        from collections import defaultdict

        catalog = defaultdict(dict)
        for release, band, key, blueprint, rune in definitions():
            category = rune.school if rune else blueprint['weapon_type'] if blueprint['kind'] == 'weapon' else 'armor'
            if rune:
                self.assertEqual(rune.circle, (2, 4, 6)[band])
            power = rune.damage if rune else blueprint.get('damage', blueprint.get('weapon_prot'))
            self.assertNotIn(category, catalog[release, band])
            catalog[release, band][category] = power
        categories = {build[0] for build in BUILDS} | {'armor'}
        for band in range(3):
            previous = {}
            for delivery in DELIVERIES:
                current = catalog[delivery.release, band]
                self.assertEqual(set(current), categories)
                for kind, power in previous.items():
                    self.assertGreater(current[kind], power)
                previous = current

    def test_active_bot_can_upgrade_an_existing_armor_in_normal_play(self):
        from .bots import tick_bot

        self.announce('barrier')
        resident = self.buyer
        resident.level = 10
        resident.is_bot = True
        resident.save(update_fields=['level', 'is_bot'])
        weapon = add_item(resident, self.blueprint('barrier', 'trail-onehand'))
        weak = ItemBluePrint.objects.create(name='Znoszony kaftan', kind='armor', weapon_prot=2)
        armor = add_item(resident, weak)
        self.assertTrue(game.equip_item(resident, weapon))
        self.assertTrue(game.equip_item(resident, armor))
        balance = resident.ore_balance
        self.assertEqual(tick_bot(resident, force_active=True), ('armor', True))
        new = resident.inventory.get(blueprint=self.blueprint('barrier', 'trail-armor'))
        resident.refresh_from_db()
        self.assertEqual(resident.ore_balance, balance - new.blueprint.base_value)
        self.assertEqual(tick_bot(resident, force_active=True), ('equip', True))
        new.refresh_from_db()
        self.assertTrue(new.is_equipped)


BUILDS = (
    ('onehand', 'OLD_CAMP', ('SHADOW', 'GUARD', 'BARON'), 'BANDITS'),
    ('twohand', 'NEW_CAMP', ('ROGUE', 'MERC', 'ELITE_MERC'), 'MERCENARIES'),
    ('bow', 'CITY_WATCH', ('K2_MILITIA', 'K2_PALADIN', 'K2_COMMANDER'), 'CITY_WATCH'),
    ('crossbow', 'ONAR_MERCS', ('K2_RECRUIT', 'K2_MERC', 'K2_CAPTAIN'), 'MERCENARIES'),
    ('fire', 'FIRE_ORDER', ('K2_ADEPT', 'K2_MAGE', 'K2_ARCHMAGE'), 'FIRE_ORDER'),
    ('water', 'NEW_CAMP', ('ROGUE', 'WATER_MAGE', 'ARCH_WATER'), 'WATER_CIRCLE'),
    ('brotherhood', 'SWAMP_CAMP', ('NOVICE', 'GURU', 'ARCH_GURU'), 'VEIL_ORDER'),
)
OPPONENTS = (
    ('g2nk_orcbiter', 'g2nk_draconian', 'k2_dragon_fire'),
    ('jark_mantis', 'jark_guardian', 'rank_jarkendar_guardian'),
    ('g2nk_orcbiter', 'g2nk_draconian', 'rank_night_watch'),
    ('jark_mantis', 'g2nk_draconian', 'g2nk_dragon_ice'),
    ('jark_mantis', 'g2nk_draconian', 'g2nk_dragon_undead'),
    ('jark_mantis', 'g2nk_draconian', 'rank_orc_standard'),
)


class ReleaseCombatMatrixTests(TestCase):
    def test_staged_gear_against_world_encounters(self):
        colony, island, race = fixture()
        call_command('seed_khorinis', stdout=StringIO())
        profiles = {}
        for style, camp, ranks, faction in BUILDS:
            for index, rank in enumerate(ranks):
                start = island if camp in ('CITY_WATCH', 'ONAR_MERCS', 'FIRE_ORDER') else colony
                profiles[style, index] = person(start, camp, rank), faction
        apply(apps, race)
        blueprints = ItemBluePrint.objects.in_bulk(GEAR, field_name='catalog_key')
        for step, (delivery, targets) in enumerate(zip(DELIVERIES, OPPONENTS, strict=True)):
            WorldRelease.objects.create(world=colony, key=delivery.release)
            for index, (band, target) in enumerate(zip(delivery.bands, targets, strict=True)):
                monster = BOSSES[target].monster if target in BOSSES else BESTIARY[target]
                prefix = f"oe-release-{delivery.release}-{('trail', 'journey', 'master')[index]}"
                for style, _, _, _ in BUILDS:
                    p, faction = profiles[style, index]
                    with self.subTest(release=delivery.release, band=index, build=style, faction=faction):
                        p.refresh_from_db()
                        expected_faction = 'MERCENARIES' if style == 'water' and index == 0 else faction
                        self.assertEqual(p.faction_membership.faction, expected_faction)
                        p.inventory.all().delete()
                        p.level = band.level
                        p.strength = p.dexterity = band.attribute + (2, 6, 15)[index]
                        p.life = 50 + 12 * p.level
                        p.current_health = p.life
                        p.mana = p.current_mana = (35, 115, 240)[index]
                        p.magic_skill = (2, 4, 6)[index]
                        p.ore_balance = band.price * 3 + 1000
                        p.onehand_skill = p.twohand_skill = p.bow_skill = p.crossbow_skill = (16, 32, 60)[index]
                        p.save()
                        if step == 1:
                            claimed_milestone(p, 'jark-portal')
                            p.refresh_from_db()
                            if hasattr(p, '_jarkendar_unlocked'):
                                del p._jarkendar_unlocked
                        self.assertTrue(game.buy_item_from_npc(p, blueprints[f'{prefix}-armor']))
                        armor = p.inventory.get(blueprint=blueprints[f'{prefix}-armor'])
                        self.assertTrue(game.equip_item(p, armor))
                        magic = style in ('fire', 'water', 'brotherhood')
                        if magic:
                            rune = purchase_magic(p, blueprints[f'{prefix}-{style}-rune'].pk)
                            self.assertTrue(rune)
                            self.assertTrue(prepare_magic(p, rune.pk))
                        else:
                            weapon = blueprints[f'{prefix}-{style}']
                            self.assertTrue(game.buy_item_from_npc(p, weapon))
                            self.assertTrue(game.equip_item(p, p.inventory.get(blueprint=weapon)))
                        p.refresh_from_db()
                        plan = combat_plan(p) if magic else None
                        self.assertEqual(bool(plan), magic)
                        for strategy, health, mana in (
                            ('rested', p.max_health, p.max_mana),
                            ('partial_resources', p.max_health * 3 // 4, p.max_mana * 2 // 3),
                        ):
                            for seed_value in (42, 79, 137):
                                p.current_health = health
                                p.current_mana = mana
                                rng = random.Random(seed_value)
                                with patch('characters.game_logic.random.randint', side_effect=rng.randint):
                                    result = game.simulate_combat(p, target, monster=monster, magic_plan=plan)
                                rounds = sum(line.startswith(f"{monster['nazwa']} pozostało ") for line in result.log)
                                self.assertGreaterEqual(rounds, 2)
                                if strategy == 'rested':
                                    self.assertTrue(result.won, (result.remaining_health, rounds))
                                    self.assertLessEqual(rounds, (12, 20, 29)[index])
                                record_scenario('release-equipment-combat', {
                                    'release': delivery.release, 'band': index, 'opponent': target,
                                    'build': style, 'faction': expected_faction, 'strategy': strategy,
                                    'seed': seed_value, 'won': result.won, 'rounds': rounds,
                                    'remaining_health': result.remaining_health,
                                })
                        if index == 2 and not magic:
                            top_weapon = add_item(p, weapon, origin='admin', rarity=4)
                            top_weapon.upgrade_level = 3
                            top_weapon.save(update_fields=['upgrade_level'])
                            self.assertTrue(game.equip_item(p, top_weapon))
                            setattr(p, style + '_skill', 100)
                            p.current_health = p.max_health
                            with patch('characters.game_logic.random.randint', return_value=1):
                                result = game.simulate_combat(p, target, monster=monster)
                            rounds = sum(line.startswith(f"{monster['nazwa']} pozostało ") for line in result.log)
                            self.assertGreaterEqual(rounds, 2)
                            record_scenario('release-tempered-weapon', {
                                'release': delivery.release, 'opponent': target, 'build': style,
                                'faction': expected_faction, 'rounds': rounds, 'won': result.won,
                            })
