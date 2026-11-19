from contextlib import ExitStack
from io import StringIO
from uuid import uuid4
from unittest.mock import patch

from django.utils import timezone

from django.core.management import call_command
from django.test import TestCase

from .bot_arrivals import ARRIVAL_INTERVAL, ARRIVAL_QUOTAS, AUTOMATIC_POPULATION_CAP, MILESTONE_KEYS, admit_next_cohort, base_bot_target
from .models import PlayerProfile, World, WorldRelease
from .scheduler_lease import SchedulerGuard


class BotArrivalTests(TestCase):
    def setUp(self):
        from .worlds import current_world
        self.colony = current_world()
        self.colony.configured = True
        self.colony.bot_count = 2
        self.colony.save(update_fields=['configured', 'bot_count'])
        self.island = World.objects.create(name='Khorinis', universe='GOTHIC_II', is_open=True, configured=True, bot_count=2)
        for world in (self.colony, self.island):
            call_command('run_bots', world=world.pk, create=2, create_only=True, stdout=StringIO())

    def join(self):
        World.objects.filter(pk__in=(self.colony.pk, self.island.pk)).update(union_key=uuid4())

    def test_arrivals_follow_milestones_and_restart_without_duplicate_accounts(self):
        release = WorldRelease.objects.create(world=self.colony, key='barrier')
        with SchedulerGuard(self.colony) as worker:
            admit_next_cohort(worker)
            self.assertEqual(PlayerProfile.objects.filter(is_bot=True).count(), 4)
            self.join()
            admit_next_cohort(worker)
        with SchedulerGuard(self.colony) as restarted:
            admit_next_cohort(restarted)

        release.refresh_from_db()
        self.assertEqual(release.bot_arrivals, 5)
        newcomers = PlayerProfile.objects.filter(user__username__startswith='arrival-').select_related('user')
        self.assertEqual(newcomers.count(), 5)
        for profile in newcomers:
            self.assertEqual((profile.level, profile.experience, profile.ore_balance, profile.magic_skill), (0, 0, 50, 0))
            self.assertEqual(profile.origin_world_id, profile.world_id)
            self.assertFalse(profile.user.has_usable_password())
            self.assertTrue(profile.bot_personality)
            self.assertFalse(profile.inventory.exists())
        for world in (self.colony, self.island):
            world.refresh_from_db()
            self.assertEqual(base_bot_target(world), 2)
            self.assertEqual(world.bot_count, PlayerProfile.objects.filter(world=world, is_bot=True).count())

    def test_at_most_one_group_per_call_and_disabled_region_stays_disabled(self):
        self.join()
        World.objects.filter(pk=self.island.pk).update(bot_count=0)
        for key in reversed(MILESTONE_KEYS):
            WorldRelease.objects.create(world=self.colony, key=key)
        with SchedulerGuard(self.colony) as worker:
            admit_next_cohort(worker)
            self.assertEqual(WorldRelease.objects.filter(bot_arrivals=5).get().key, 'barrier')
            for batch in range(1, ARRIVAL_QUOTAS['barrier'] // 5 + 1):
                with patch('characters.bot_arrivals.timezone.now', return_value=timezone.now() + batch * ARRIVAL_INTERVAL):
                    admit_next_cohort(worker)
        self.assertEqual(WorldRelease.objects.get(key='barrier').bot_arrivals, ARRIVAL_QUOTAS['barrier'])
        self.assertEqual(WorldRelease.objects.get(key='jarkendar').bot_arrivals, 5)
        self.assertFalse(PlayerProfile.objects.filter(world=self.island, user__username__startswith='arrival-').exists())

    def test_manual_population_at_cap_is_preserved(self):
        self.join()
        World.objects.filter(pk__in=(self.colony.pk, self.island.pk)).update(bot_count=AUTOMATIC_POPULATION_CAP // 2)
        release = WorldRelease.objects.create(world=self.colony, key='barrier')
        with SchedulerGuard(self.colony) as worker:
            admit_next_cohort(worker)
        release.refresh_from_db()
        self.island.refresh_from_db()
        self.assertEqual(release.bot_arrivals, 0)
        self.assertEqual(self.island.bot_count, AUTOMATIC_POPULATION_CAP // 2)

    def test_fresh_queue_alternates_regions_and_keeps_waiting_order(self):
        from .bot_scheduler import BotScheduler
        from .realm_scheduler import ParallelRealms

        World.objects.filter(pk__in=(self.colony.pk, self.island.pk)).update(bot_personality_cycles=False)
        with ExitStack() as cleanup, SchedulerGuard(self.colony) as worker:
            scheduler = BotScheduler(clock=lambda: 0)
            scheduler.population(ParallelRealms().sync(worker, cleanup))
            worlds = dict(PlayerProfile.objects.filter(pk__in=scheduler.queue).values_list('pk', 'world_id'))
            self.assertEqual([worlds[pk] for pk in scheduler.queue],
                             [self.colony.pk, self.island.pk, self.colony.pk, self.island.pk])
            prior = list(scheduler.queue)
            scheduler.population(reversed(prior))
            self.assertEqual(list(scheduler.queue), prior)
