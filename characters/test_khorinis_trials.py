from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import transaction
from django.test import SimpleTestCase, TestCase

from .camp_progression import (
    BY_RANK, KHORINIS_RANKS, accept_camp_quest, promote_in_camp, rank_cards, record_camp_event,
)
from .models import CampGuild, CampQuest, World
from .realms import world_scope
from .story_gates import requirements
from .testing_story import claimed_milestone


class KhorinisTrialCatalogTests(SimpleTestCase):
    def test_every_island_trial_has_its_own_objectives_at_ordinary_colony_costs(self):
        self.assertEqual(len(KHORINIS_RANKS), 12)
        targets = {frozenset(goal.event for goal in rank.objectives) for rank in KHORINIS_RANKS}
        self.assertEqual(len(targets), 12)
        colony = [rank for rank in BY_RANK.values() if rank.key not in {r.key for r in KHORINIS_RANKS}]
        for rank in KHORINIS_RANKS:
            peers = [r for r in colony if r.tier == rank.tier]
            self.assertLessEqual(min(r.level for r in peers), rank.level)
            self.assertLessEqual(rank.level, max(r.level for r in peers))
            self.assertLessEqual(min(r.cost for r in peers), rank.cost)
            self.assertLessEqual(rank.cost, max(r.cost for r in peers))

    def test_last_trials_are_comparable_in_base_enemy_health_to_colony_paths(self):
        from .bestiary import BESTIARY
        from .bosses import BOSSES

        def enemy_health(rank):
            return sum(goal.count * (BESTIARY[target]['life'] if kind == 'hunt' else BOSSES[target].life)
                       for goal in rank.objectives for kind, _, target in [goal.event.partition(':')]
                       if kind in {'hunt', 'boss'})

        for island, colony in [('K2_COMMANDER', 'BARON'), ('K2_ARCHMAGE', 'ARCH_FIRE'),
                               ('K2_CAPTAIN', 'ELITE_MERC')]:
            with self.subTest(island=island, colony=colony):
                ratio = enemy_health(BY_RANK[island]) / enemy_health(BY_RANK[colony])
                self.assertGreaterEqual(ratio, .85)
                self.assertLessEqual(ratio, 1.15)


class KhorinisTrialTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.island = World.objects.create(name='Khorinis', universe='GOTHIC_II', is_open=True)
        for camp in ('CITY_WATCH', 'FIRE_ORDER', 'ONAR_MERCS'):
            CampGuild.objects.create(world=cls.island, camp=camp)
        call_command('seed_khorinis', verbosity=0)

    def recruit(self, name, camp, guild, *, level, ore):
        with world_scope(self.island):
            hero = User.objects.create_user(name).playerprofile
        hero.camp = camp
        hero.guild = guild
        hero.level = level
        hero.ore_balance = ore
        hero.dexterity = 30
        hero.save()
        return hero

    def qualify(self, hero, rank):
        for key in requirements(hero, rank.tier):
            claimed_milestone(hero, key)
        hero.__dict__.pop('_story_gate_claimed', None)

    def test_accepted_old_trial_retains_its_objectives_level_and_price(self):
        rank = BY_RANK['K2_PALADIN']
        hero = self.recruit('old-khorinis', rank.camp, 'K2_MILITIA', level=8, ore=100)
        hero.strength = 25
        hero.save(update_fields=['strength'])
        self.qualify(hero, rank)
        quest = CampQuest.objects.create(profile=hero, rank_key=rank.key,
                                        progress={'train:strength': 2, 'hunt:k2_field_raider': 2})
        card = next(c for c in rank_cards(hero) if c['rank'].key == rank.key)
        self.assertEqual((card['rank'].level, card['rank'].cost), (8, 100))
        self.assertFalse(promote_in_camp(hero, rank.key))
        with transaction.atomic():
            record_camp_event(hero, 'hunt:k2_field_raider')
        self.assertTrue(promote_in_camp(hero, rank.key))
        quest.refresh_from_db()
        self.assertEqual(quest.progress['hunt:k2_field_raider'], 3)
        hero.refresh_from_db()
        self.assertEqual((hero.guild, hero.ore_balance), (rank.key, 0))

    def test_onar_archer_uses_dexterity_and_still_needs_story_and_trial(self):
        rank = BY_RANK['K2_MERC']
        hero = self.recruit('onar-archer-trial', rank.camp, 'K2_RECRUIT', level=8, ore=100)
        self.assertFalse(accept_camp_quest(hero, rank.key))
        self.qualify(hero, rank)
        self.assertTrue(accept_camp_quest(hero, rank.key))
        self.assertFalse(promote_in_camp(hero, rank.key))
        with transaction.atomic():
            for goal in rank.objectives:
                for _ in range(goal.count):
                    record_camp_event(hero, goal.event)
        self.assertTrue(promote_in_camp(hero, rank.key))
        self.assertFalse(promote_in_camp(hero, rank.key))
        hero.refresh_from_db()
        self.assertEqual((hero.guild, hero.strength, hero.ore_balance), (rank.key, 10, 0))
