from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase, SimpleTestCase
from django.urls import reverse
from django.utils import timezone
from .models import CampQuest, PlayerProfile
from .camp_progression import RANKS, BY_RANK, accept_camp_quest, promote_in_camp, abandon_camp_quest
from .locations import LOCATIONS
from .bestiary import BESTIARY
from . import game_logic as game


class CampCatalogTests(SimpleTestCase):
    def test_all_branches_have_reachable_parents_and_objectives(self):
        self.assertEqual(len(RANKS), 18)
        self.assertEqual(len(BY_RANK), len(RANKS))
        for rank in RANKS:
            self.assertTrue(rank.objectives)
            for parent in rank.parents:
                if parent != "NONE":
                    self.assertEqual(BY_RANK[parent].camp, rank.camp)
                    self.assertLess(BY_RANK[parent].level, rank.level)
            for goal in rank.objectives:
                self.assertGreater(goal.count, 0)
                if goal.event.startswith("hunt:"):
                    monster = goal.event.split(":")[1]
                    self.assertIn(monster, BESTIARY)
                    self.assertTrue(any(monster in loc.monsters and loc.level <= rank.level and not loc.min_tier for loc in LOCATIONS), rank.key)


class CampProgressionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("camp-player")
        self.profile = self.user.playerprofile
        self.profile.camp = "OLD_CAMP"
        self.profile.save()
        self.client.force_login(self.user)

    def mine(self):
        self.assertTrue(game.start_mining(self.profile, 1))
        self.profile.action_end_time = timezone.now() - timedelta(seconds=1)
        self.profile.save(update_fields=["action_end_time"])
        self.assertTrue(game.claim_ore_reward(self.profile))

    def test_initial_quest_accept_mine_promote_and_replay(self):
        self.mine()  # Activities before accepting do not count.
        self.assertTrue(accept_camp_quest(self.profile, "DIGGER"))
        self.assertFalse(promote_in_camp(self.profile, "DIGGER"))
        self.assertEqual(CampQuest.objects.get().progress, {})
        self.mine()
        self.assertEqual(CampQuest.objects.get().progress, {"mine": 1})
        self.assertTrue(promote_in_camp(self.profile, "DIGGER"))
        self.assertFalse(promote_in_camp(self.profile, "DIGGER"))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.guild, "DIGGER")
        self.assertIsNotNone(CampQuest.objects.get().promoted_at)

    def test_each_rank_can_be_completed_using_real_domain_actions(self):
        for index, rank in enumerate(RANKS):
            with self.subTest(rank=rank.key):
                profile = User.objects.create_user("rank-" + str(index)).playerprofile
                profile.camp, profile.guild, profile.level = rank.camp, rank.parents[0], rank.level
                profile.strength = profile.dexterity = profile.mana = 100
                profile.skill_points = 100
                profile.ore_balance = 10000
                profile.max_energy = profile.current_energy = 10000
                profile.save()
                self.assertTrue(accept_camp_quest(profile, rank.key))
                for goal in rank.objectives:
                    for _ in range(goal.count):
                        kind, _, key = goal.event.partition(":")
                        if kind == "hunt":
                            habitat = next(loc for loc in LOCATIONS if key in loc.monsters and loc.accessible(profile))
                            with patch("characters.game_logic.simulate_combat", return_value=(True, ["Test victory"])):
                                self.assertIsNot(game.execute_hunt(profile, key, habitat.key), False)
                        elif kind == "boss":
                            with patch("characters.game_logic.simulate_combat", return_value=(True, ["Test victory"])):
                                self.assertTrue(game.execute_boss(profile, key).won)
                        elif kind == "train":
                            self.assertTrue(game.train_attribute(profile, key))
                        else:
                            self.assertTrue(game.start_mining(profile, 1))
                            profile.action_end_time = timezone.now() - timedelta(seconds=1)
                            profile.save(update_fields=["action_end_time"])
                            self.assertTrue(game.claim_ore_reward(profile))
                profile.refresh_from_db()
                balance = profile.ore_balance
                self.assertTrue(promote_in_camp(profile, rank.key))
                profile.refresh_from_db()
                self.assertEqual((profile.guild, profile.ore_balance), (rank.key, balance - rank.cost))
                self.assertFalse(promote_in_camp(profile, rank.key))
                profile.refresh_from_db()
                self.assertEqual(profile.ore_balance, balance - rank.cost)

    def prepare_shadow_quest(self):
        self.profile.guild = "DIGGER"
        self.profile.level = 3
        self.profile.strength = 15
        self.profile.ore_balance = 30
        self.profile.save()
        self.assertTrue(accept_camp_quest(self.profile, "SHADOW"))
        CampQuest.objects.filter(profile=self.profile).update(progress={"hunt:scavenger": 3, "hunt:wolf": 2})

    def test_requirements_are_rechecked_against_database(self):
        self.prepare_shadow_quest()
        for field, value in [("level", 2), ("strength", 14), ("ore_balance", 29)]:
            with self.subTest(field=field):
                original = getattr(self.profile, field)
                PlayerProfile.objects.filter(pk=self.profile.pk).update(**{field: value})
                self.assertFalse(promote_in_camp(self.profile, "SHADOW"))
                self.profile.refresh_from_db()
                self.assertEqual(self.profile.guild, "DIGGER")
                PlayerProfile.objects.filter(pk=self.profile.pk).update(**{field: original})
                self.profile.refresh_from_db()

    def test_foreign_camp_skipped_ranks_duplicate_and_unknown_quests_rejected(self):
        for key in ["MOLE", "PICKER", "GUARD", "ARCH_FIRE", "unknown"]:
            self.assertFalse(accept_camp_quest(self.profile, key))
        self.assertTrue(accept_camp_quest(self.profile, "DIGGER"))
        self.assertFalse(accept_camp_quest(self.profile, "DIGGER"))
        self.assertEqual(CampQuest.objects.count(), 1)

    def test_branch_exclusivity_and_abandonment(self):
        self.profile.guild = "SHADOW"
        self.profile.save()
        self.assertTrue(accept_camp_quest(self.profile, "GUARD"))
        self.assertFalse(accept_camp_quest(self.profile, "FIRE_MAGE"))
        self.assertTrue(abandon_camp_quest(self.profile, "GUARD"))
        self.assertTrue(accept_camp_quest(self.profile, "FIRE_MAGE"))
        self.profile.guild = "GUARD"
        self.profile.save()
        self.assertFalse(promote_in_camp(self.profile, "FIRE_MAGE"))

    def test_defeats_failed_actions_and_other_players_do_not_advance_quest(self):
        self.prepare_shadow_quest()
        CampQuest.objects.filter(profile=self.profile).update(progress={})
        other = User.objects.create_user("other-camp-player").playerprofile
        with patch("characters.game_logic.simulate_combat", return_value=(False, ["Defeat"])):
            game.execute_hunt(self.profile, "scavenger")
        with patch("characters.game_logic.simulate_combat", return_value=(True, ["Victory"])):
            game.execute_hunt(other, "scavenger")
        self.assertFalse(game.claim_ore_reward(self.profile))
        self.assertEqual(CampQuest.objects.get(profile=self.profile).progress, {})

    def test_progress_is_capped_and_rollback_is_atomic(self):
        self.prepare_shadow_quest()
        with patch("characters.game_logic.simulate_combat", return_value=(True, ["Victory"])):
            game.execute_hunt(self.profile, "scavenger")
        self.assertEqual(CampQuest.objects.get().progress["hunt:scavenger"], 3)
        before = self.profile.ore_balance
        with patch.object(CampQuest, "save", side_effect=RuntimeError("storage failure")):
            with self.assertRaises(RuntimeError):
                promote_in_camp(self.profile, "SHADOW")
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.guild, self.profile.ore_balance), ("DIGGER", before))

    def test_form_cannot_inject_progress_or_another_players_quest(self):
        self.client.post(reverse("camp_page"), {"action": "accept", "rank": "DIGGER", "progress": 99999})
        self.client.post(reverse("camp_page"), {"action": "promote", "rank": "DIGGER", "progress": 99999})
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.guild, "NONE")
        self.assertEqual(CampQuest.objects.get().progress, {})

    def test_rank_gates_enforced_for_get_and_post_and_other_camps(self):
        for loc in (loc for loc in LOCATIONS if loc.min_tier):
            self.profile.level = 30
            self.profile.camp = loc.camps[0]
            self.profile.guild = "NONE"
            self.profile.save()
            url = reverse(loc.route) + "?location=" + loc.key
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url).status_code, 403)
            rank = next(rank for rank in RANKS if rank.camp == self.profile.camp and rank.tier >= loc.min_tier)
            self.profile.guild = rank.key
            self.profile.save()
            self.assertEqual(self.client.get(url).status_code, 200)
            self.profile.camp = "NONE"
            self.profile.save()
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_camp_page_requires_login_and_displays_all_branch_requirements(self):
        self.assertContains(self.client.get(reverse("camp_page")), "Przyjmij zadanie")
        self.assertContains(self.client.get(reverse("camp_page") + "?camp=NEW_CAMP"), "Mag Wody")
        self.assertEqual(self.client.get(reverse("camp_page") + "?camp=unknown").status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("camp_page")).status_code, 302)

    def test_strength_training_improves_normal_combat_damage(self):
        with patch("characters.game_logic.random.randint", return_value=100):
            _, before = game.simulate_combat(self.profile, "scavenger")
            self.profile.strength += 10
            _, after = game.simulate_combat(self.profile, "scavenger")
        self.assertIn("8 obrażeń", before[0])
        self.assertIn("18 obrażeń", after[0])

    def test_quest_storage_failure_rolls_back_hunt_cost_and_experience(self):
        self.prepare_shadow_quest()
        before = (self.profile.current_energy, self.profile.experience)
        with patch("characters.game_logic.simulate_combat", return_value=(True, ["Victory"])), patch("characters.camp_progression.record_camp_event", side_effect=RuntimeError("storage failure")):
            with self.assertRaises(RuntimeError):
                game.execute_hunt(self.profile, "scavenger")
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.current_energy, self.profile.experience), before)

    def test_trained_character_can_defeat_every_species_without_mocked_combat(self):
        self.profile.life = 500
        self.profile.strength = 250
        self.profile.onehand_skill = 0
        for key in BESTIARY:
            with self.subTest(monster=key):
                won, log = game.simulate_combat(self.profile, key)
                self.assertTrue(won)
                self.assertTrue(log)
