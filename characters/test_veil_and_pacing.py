from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.apps import apps
from django.core.management import call_command
from django.db import transaction
from django.test import TestCase

from .barrier import travel
from .faction_advancement import BY_KEY, rank_for
from .faction_choice import choose
from .faction_succession_v2 import apply, reform
from .factions import RANK_NAMES
from .locations import BY_KEY as LOCATIONS
from .models import BarrierEvent, CampGuild, CampQuest, FactionRankProgress, WorldRelease
from .story_quests import accept_story
from .test_faction_succession import fixture, person, succeed
from .testing_story import claimed_milestone
from .world_releases import milestone_wait, sync_releases


class VeilAndPacingTests(TestCase):
    def setUp(self):
        self.c, self.i, self.race = fixture()
        call_command('seed_khorinis', stdout=StringIO())

    def test_new_veil_guild_preserves_school_and_distinct_promotion_attributes(self):
        guru = person(self.c, 'SWAMP_CAMP', 'ARCH_GURU')
        guard = person(self.c, 'SWAMP_CAMP', 'TEMPLAR')
        old_guild = CampGuild.objects.get(world=self.c, camp='SWAMP_CAMP')
        old_guild.treasury = 77
        old_guild.save(update_fields=['treasury'])
        with transaction.atomic():
            apply(apps, self.race)
        for p in (guru, guard):
            p.refresh_from_db()
            self.assertEqual(p.faction_membership.guild_id, old_guild.pk)
            self.assertEqual(p.faction_membership.faction, 'VEIL_ORDER')
            self.assertFalse(choose(p, 'FIRE_ORDER'))
        old_guild.refresh_from_db()
        self.assertEqual(old_guild.treasury, 77)
        self.assertEqual(len(RANK_NAMES['VEIL_ORDER']), 8)
        rank = BY_KEY['ADV_VEIL_ORDER_4']
        self.assertEqual(rank_for(guru, rank).attribute, 'mana')
        self.assertEqual(rank_for(guard, rank).attribute, 'martial')
        from .magic import circle_cap, school_for
        self.assertEqual(circle_cap(guru), 6)
        self.assertEqual(school_for(guru)[0], 'brotherhood')

    def test_old_choice_keeps_paid_tier_and_open_promotion(self):
        guru = person(self.c, 'SWAMP_CAMP', 'ARCH_GURU')
        succession = succeed(self.race)
        self.assertTrue(choose(guru, 'WATER_CIRCLE'))
        member = guru.faction_membership
        FactionRankProgress.objects.create(membership=member, tier=4)
        quest = CampQuest.objects.create(profile=guru, rank_key='ADV_WATER_CIRCLE_5', progress={'hunt:orc_veteran': 2})
        from .equipment import add_item
        from .models import ItemBluePrint
        foreign, _ = ItemBluePrint.objects.get_or_create(catalog_key='oe-water-g1-waterlance-rune', defaults={'name':'Runa Wody','kind':'rune'})
        item = add_item(guru, foreign)
        guru.prepared_magic = item
        guru.save(update_fields=['prepared_magic'])
        original = list(guru.inventory.values())
        reform(apps, succession)
        guru.refresh_from_db()
        quest.refresh_from_db()
        self.assertEqual(guru.faction_membership.faction, 'VEIL_ORDER')
        self.assertEqual(guru.faction_membership.rank_progress.tier, 4)
        self.assertEqual(guru.faction_membership.choice.destination, 'WATER_CIRCLE')
        self.assertEqual((quest.rank_key, quest.progress), ('ADV_VEIL_ORDER_5', {'hunt:orc_veteran': 2}))
        self.assertIsNone(guru.prepared_magic_id)
        self.assertEqual(list(guru.inventory.values()), original)

    def test_dexter_headquarters_has_no_early_portal_access(self):
        bandit = person(self.c, 'OLD_CAMP', 'BARON')
        bandit.level = 35
        bandit.save(update_fields=['level'])
        with transaction.atomic():
            apply(apps, self.race)
        bandit.refresh_from_db()
        self.assertTrue(travel(bandit, self.i.pk))
        self.assertTrue(LOCATIONS['dexter_tower'].accessible(bandit))
        self.assertFalse(LOCATIONS['jark_bandits'].accessible(bandit))

    def test_real_world_requires_earned_milestones_and_elapsed_stage_time(self):
        p = person(self.c, 'OLD_CAMP', 'BARON')
        p.level = 50
        p.save(update_fields=['level'])
        BarrierEvent.objects.create(race=self.race, kind='joined')
        start = self.race.joined_at
        self.assertEqual(sync_releases(self.c, start), {'foundations', 'barrier'})
        portal = self.i.pk
        self.assertTrue(travel(p, portal))
        from .models import StoryQuest
        quest = StoryQuest.objects.get(key='jark-portal')
        with patch('django.utils.timezone.now', return_value=start + timedelta(hours=47)):
            self.assertFalse(accept_story(p, quest.pk))
            self.assertEqual(milestone_wait(self.c.pk, 'jark-portal'), 3600)
        elapsed = start + timedelta(days=2)
        self.assertNotIn('jarkendar', sync_releases(self.c, elapsed))
        with patch('django.utils.timezone.now', return_value=elapsed):
            claimed_milestone(p, 'jark-portal')
            claimed_milestone(p, 'nk-scouts')
        self.assertIn('jarkendar', sync_releases(self.c, elapsed))
        self.assertNotIn('night', sync_releases(self.c, elapsed))
        self.assertIn('night', sync_releases(self.c, elapsed + timedelta(days=1)))
        self.assertEqual(WorldRelease.objects.get(world=self.c, key='jarkendar').released_at, elapsed)
