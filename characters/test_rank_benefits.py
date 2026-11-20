from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from uuid import uuid4

from django.apps import apps
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from .barrier import travel
from .bots import tick_bot
from .camp_progression import BY_RANK, rank_cards, accept_camp_quest, promote_in_camp
from .faction_advancement import BY_KEY, cards
from .frontier import patrol
from .models import (
    CampQuest, FrontierProgress, FrontierRecord, RegionalFrontierProgress, StoryQuest, WorldRelease,
)
from .rank_benefits import PATROL_LIMITS, patrol_permit, playable_patrol_depth, rank_benefits
from .regional_endgame import fee
from .test_faction_succession import fixture, person
from .testing_story import claimed_milestone, promotion_prerequisites
from .world_management import seed_clean_world
from .faction_succession_v2 import apply


class RankPatrolTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_clean_world()
        cls.colony, cls.island, cls.race = fixture()
        call_command('seed_khorinis', stdout=StringIO())
        for key in ('barrier', 'jarkendar', 'dragons', 'irdorath'):
            WorldRelease.objects.get_or_create(world=cls.colony, key=key)

    def resident(self, world, camp, guild):
        p = person(world, camp, guild)
        p.level = 60
        p.strength = p.dexterity = 6000
        p.mana = 5000
        p.life = p.current_health = 5000
        p.ore_balance = 50000
        p.save()
        return p

    def test_every_native_rank_advertises_a_higher_patrol_permit(self):
        self.assertEqual(sorted(set(PATROL_LIMITS)), list(PATROL_LIMITS))
        for rank in BY_RANK.values():
            world = self.colony if rank.camp in ('OLD_CAMP', 'NEW_CAMP', 'SWAMP_CAMP') else self.island
            with self.subTest(rank=rank.key):
                p = person(world, rank.camp, rank.key)
                self.assertEqual(patrol_permit(p), PATROL_LIMITS[rank.tier])
                card = next(card for card in rank_cards(p) if card['rank'].key == rank.key)
                self.assertEqual(card['benefits'], rank_benefits(rank.tier, camp=rank.camp, guild=rank.key))

    def test_promotion_applies_an_existing_victory_without_spending_on_a_denial(self):
        p = self.resident(self.colony, 'OLD_CAMP', 'DIGGER')
        promotion_prerequisites(p, 1)
        progress = FrontierProgress.objects.create(profile=p, unlocked=PATROL_LIMITS[0])
        won = patrol(p, PATROL_LIMITS[0], uuid4())
        self.assertTrue(won.won)
        progress.refresh_from_db()
        self.assertEqual(progress.unlocked, PATROL_LIMITS[0] + 1)
        self.assertEqual(playable_patrol_depth(p, progress), PATROL_LIMITS[0])
        p.refresh_from_db()
        later = timezone.now() + timedelta(minutes=6)
        with patch('django.utils.timezone.now', return_value=later):
            from .game_logic import refresh_player

            refresh_player(p)
            before = p.ore_balance, p.current_energy, p.experience
            self.assertFalse(patrol(p, PATROL_LIMITS[0] + 1, uuid4()))
            self.assertEqual(patrol(p, PATROL_LIMITS[0], won.request_key).pk, won.pk)
        p.refresh_from_db()
        self.assertEqual((p.ore_balance, p.current_energy, p.experience), before)
        self.assertEqual(FrontierRecord.objects.filter(profile=p).count(), 1)
        self.client.force_login(p.user)
        page = self.client.get(reverse('frontier_page'))
        self.assertContains(page, '<strong>Cień</strong>', html=True)
        self.assertEqual(page.context['depth'], PATROL_LIMITS[0])
        self.assertTrue(accept_camp_quest(p, 'SHADOW'))
        CampQuest.objects.filter(profile=p, rank_key='SHADOW').update(progress={'hunt:wolf': 2, 'hunt:scavenger': 3})
        self.assertTrue(promote_in_camp(p, 'SHADOW'))
        self.assertEqual(playable_patrol_depth(p, progress), PATROL_LIMITS[0] + 1)
        with patch('django.utils.timezone.now', return_value=later):
            self.assertTrue(patrol(p, PATROL_LIMITS[0] + 1, uuid4()).won)

    def test_each_advanced_rank_opens_more_and_rank_eight_permits_all_regional_depths(self):
        origins = (
            (self.colony, 'OLD_CAMP', 'BARON', 'BANDITS'),
            (self.colony, 'NEW_CAMP', 'ARCH_WATER', 'WATER_CIRCLE'),
            (self.colony, 'SWAMP_CAMP', 'ARCH_GURU', 'VEIL_ORDER'),
            (self.island, 'CITY_WATCH', 'K2_COMMANDER', 'CITY_WATCH'),
            (self.island, 'FIRE_ORDER', 'K2_ARCHMAGE', 'FIRE_ORDER'),
            (self.island, 'ONAR_MERCS', 'K2_CAPTAIN', 'MERCENARIES'),
        )
        actors = [(self.resident(world, camp, native), faction) for world, camp, native, faction in origins]
        apply(apps, self.race)
        for p, faction in actors:
            with self.subTest(faction=faction):
                p.refresh_from_db()
                self.assertEqual(p.faction_membership.faction, faction)
                self.assertEqual(patrol_permit(p), PATROL_LIMITS[3])
                self.assertEqual(fee(1, p), 12)
                claimed_milestone(p, 'nk-undead')
                self.assertTrue(travel(p, self.island.pk))
                progress = RegionalFrontierProgress.objects.create(profile=p, track='khorinis', unlocked=100)
                for tier in range(4, 8):
                    key = f'ADV_{faction}_{tier}'
                    self.assertTrue(accept_camp_quest(p, key))
                    quest = p.camp_quests.get(rank_key=key)
                    quest.progress.update({goal.event: goal.count for goal in BY_KEY[key].objectives})
                    quest.save(update_fields=['progress'])
                    self.assertTrue(promote_in_camp(p, key))
                    self.assertEqual(playable_patrol_depth(p, progress), PATROL_LIMITS[tier])
                    self.assertEqual(fee(1, p), 12 - 2 * (tier - 3))
                    card = next(card for card in cards(p) if card['rank'].key == key)
                    self.assertEqual(card['benefits'], rank_benefits(tier))
                won = patrol(p, 100, uuid4(), 'khorinis')
                self.assertTrue(won.won)
                self.assertEqual(won.snapshot['entry_fee'], 82)

    def test_bot_chooses_only_a_permitted_depth(self):
        p = self.resident(self.colony, 'OLD_CAMP', 'DIGGER')
        p.is_bot = True
        p.save(update_fields=['is_bot'])
        FrontierProgress.objects.create(profile=p, unlocked=PATROL_LIMITS[0] + 1)

        class PatrolPolicy:
            def choose(self, observation):
                return 'patrol', observation.patrol_depth

        self.assertEqual(tick_bot(p, policy=PatrolPolicy(), force_active=True), ('patrol', True))
        self.assertEqual(p.patrols.get().depth, PATROL_LIMITS[0])

    def test_native_expedition_needs_rank_and_the_correct_region(self):
        from .game_logic import execute_boss
        from .locations import BY_KEY

        p = self.resident(self.colony, 'OLD_CAMP', 'DIGGER')
        site = BY_KEY['rank_gorge_raider']
        url = reverse('boss_page') + '?location=' + site.key
        self.client.force_login(p.user)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {'request_key': uuid4()}).status_code, 403)
        self.assertFalse(execute_boss(p, site.key))
        self.assertFalse(p.boss_attempts.exists())
        p.guild = 'SHADOW'
        p.save(update_fields=['guild'])
        self.assertEqual(self.client.get(url).status_code, 200)
        key = uuid4()
        won = execute_boss(p, site.key, key)
        self.assertTrue(won.won)
        self.assertEqual(execute_boss(p, site.key, key).pk, won.pk)
        self.assertEqual(p.boss_attempts.count(), 1)
        self.assertTrue(travel(p, self.island.pk))
        self.assertFalse(site.accessible(p))

    def test_archives_are_exclusive_to_earned_archmage_paths(self):
        from .game_logic import execute_boss
        from .locations import BY_KEY

        for world, camp, regular, martial, arch, key in (
            (self.colony, 'OLD_CAMP', 'FIRE_MAGE', 'BARON', 'ARCH_FIRE', 'rank_valley_archive'),
            (self.island, 'FIRE_ORDER', 'K2_MAGE', None, 'K2_ARCHMAGE', 'rank_monastery_archive'),
        ):
            p = self.resident(world, camp, regular)
            self.assertFalse(BY_KEY[key].accessible(p))
            self.assertFalse(execute_boss(p, key))
            if martial:
                p.guild = martial
                p.save(update_fields=['guild'])
                self.assertFalse(BY_KEY[key].accessible(p))
            p.guild = arch
            p.save(update_fields=['guild'])
            self.assertTrue(BY_KEY[key].accessible(p))
            self.assertTrue(execute_boss(p, key).won)

    def test_late_boss_needs_both_the_release_and_the_highest_rank(self):
        from .game_logic import execute_boss
        from .locations import BY_KEY as locations

        p = self.resident(self.colony, 'OLD_CAMP', 'BARON')
        apply(apps, self.race)
        p.refresh_from_db()
        claimed_milestone(p, 'nk-undead')
        site = locations['rank_orc_standard']
        self.assertFalse(site.accessible(p))
        for tier in range(4, 8):
            key = f'ADV_BANDITS_{tier}'
            self.assertTrue(accept_camp_quest(p, key))
            quest = p.camp_quests.get(rank_key=key)
            quest.progress.update({goal.event: goal.count for goal in BY_KEY[key].objectives})
            quest.save(update_fields=['progress'])
            self.assertTrue(promote_in_camp(p, key))
        self.assertFalse(site.accessible(p))
        self.client.force_login(p.user)
        self.assertContains(self.client.get(reverse('locations_page')), 'Dostęp od odsłony „Orkowie u bram”')
        WorldRelease.objects.get_or_create(world=self.colony, key='orc-war')
        self.assertTrue(site.accessible(p))
        self.assertTrue(execute_boss(p, site.key).won)

    def test_idle_bot_uses_rank_expedition_through_normal_boss_action(self):
        StoryQuest.objects.update(enabled=False)
        p = self.resident(self.colony, 'OLD_CAMP', 'SHADOW')
        p.is_bot = True
        p.bot_turn = 4
        p.save(update_fields=['is_bot', 'bot_turn'])
        self.assertEqual(tick_bot(p, force_active=True), ('boss', True))
        self.assertTrue(p.boss_attempts.filter(boss_key='rank_gorge_raider', won=True).exists())


class PatrolPermitMigrationTests(TransactionTestCase):
    def test_preserves_preexisting_unlocked_depth_per_track(self):
        old_node = [('characters', '0062_khorinis_campaign_hunting_materials')]
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes('characters')
        executor.migrate(old_node)
        old = executor.loader.project_state(old_node).apps
        try:
            worlds = old.get_model('characters', 'World').objects
            world = worlds.filter(is_current=True).first() or worlds.create(name='Stary świat', is_current=True)
            user = old.get_model('auth', 'User').objects.create(username='old-patrol')
            profile = old.get_model('characters', 'PlayerProfile').objects.create(
                user_id=user.pk, world_id=world.pk, camp='OLD_CAMP', guild='BARON',
            )
            old.get_model('characters', 'FrontierProgress').objects.create(
                profile_id=profile.pk, unlocked=32, wins=40,
            )
            old.get_model('characters', 'RegionalFrontierProgress').objects.create(
                profile_id=profile.pk, track='valley', unlocked=64, wins=80,
            )
            MigrationExecutor(connection).migrate(latest)
            legacy = FrontierProgress.objects.get(profile_id=profile.pk)
            valley = RegionalFrontierProgress.objects.get(profile_id=profile.pk, track='valley')
            self.assertEqual((legacy.unlocked, legacy.rank_access_floor, legacy.wins), (32, 32, 40))
            self.assertEqual((valley.unlocked, valley.rank_access_floor, valley.wins), (64, 64, 80))
            fresh_track = RegionalFrontierProgress(profile_id=profile.pk, track='khorinis', unlocked=PATROL_LIMITS[3] + 1)
            self.assertEqual(playable_patrol_depth(legacy.profile, fresh_track), PATROL_LIMITS[3])
            self.assertEqual(playable_patrol_depth(legacy.profile, valley), 64)
            valley.unlocked += 1
            self.assertEqual(playable_patrol_depth(legacy.profile, valley), 64)
        finally:
            MigrationExecutor(connection).migrate(latest)
