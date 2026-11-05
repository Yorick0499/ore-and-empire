from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import StoryQuest, StoryRun, ItemBluePrint, OwnedItem, PremiumEntry
from .story_quests import (accept_story, activate_story, choose_story, travel_story,
                           claim_story, ready, validate_definition)
from .bots import tick_bot
from . import game_logic as game


def goal(kind, target=None, **kwargs):
    data = {'id': kind, 'kind': kind, 'label': 'Cel ' + kind, **kwargs}
    if target is not None: data['target'] = target
    return data


class StoryQuestTests(TestCase):
    def setUp(self):
        call_command('seed_world', stdout=StringIO())
        self.profile = User.objects.create_user('hero').playerprofile
        self.other = User.objects.create_user('other').playerprofile
        self.weapon = ItemBluePrint.objects.get(name='Zardzewiały miecz')

    def quest(self, **kwargs):
        data = {'key': 'first', 'title': 'Pierwsza przysługa', 'description': 'Autorska historia.',
                'objectives': [goal('talk', options={'help': 'Pomogę', 'ask': 'Zapytam o nagrodę'})],
                'rewards': {'ore': 20, 'experience': 50, 'premium': 1}}
        data.update(kwargs)
        return StoryQuest.objects.create(**data)

    def active(self, quest):
        run = accept_story(self.profile, quest.pk)
        self.assertTrue(run)
        self.assertEqual(run.status, 'accepted')
        self.assertTrue(activate_story(self.profile, run.pk))
        run.refresh_from_db()
        return run

    def test_chain_gates_choices_and_single_reward(self):
        first = self.quest()
        second = self.quest(key='second', prerequisites=['first'], required_choices={'first': {'talk': 'help'}})
        self.assertFalse(accept_story(self.profile, second.pk))
        run = self.active(first)
        self.assertFalse(choose_story(self.profile, run.pk, 'talk', 'forged'))
        self.assertTrue(choose_story(self.profile, run.pk, 'talk', 'help'))
        self.assertFalse(choose_story(self.profile, run.pk, 'talk', 'ask'))
        self.assertFalse(claim_story(self.other, run.pk))
        self.assertTrue(claim_story(self.profile, run.pk))
        self.assertFalse(claim_story(self.profile, run.pk))
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.ore_balance, self.profile.premium_balance), (70, 1))
        self.assertEqual(PremiumEntry.objects.count(), 1)
        self.assertTrue(accept_story(self.profile, second.pk))
        self.assertFalse(accept_story(self.profile, first.pk))

    def test_accepted_snapshot_survives_definition_change_and_disable(self):
        quest = self.quest()
        run = self.active(quest)
        quest.objectives = [goal('wait', seconds=9999)]
        quest.rewards = {'ore': 9999}
        quest.enabled = False
        quest.version = 2
        quest.save()
        self.assertTrue(choose_story(self.profile, run.pk, 'talk', 'help'))
        self.assertTrue(claim_story(self.profile, run.pk))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.ore_balance, 70)
        self.assertFalse(accept_story(self.other, quest.pk))

    def test_mine_and_won_hunt_count_only_after_activation(self):
        quest = self.quest(objectives=[goal('mine'), goal('hunt', 'young_scavenger')])
        run = accept_story(self.profile, quest.pk)
        game.start_mining(self.profile, 1)
        self.profile.action_end_time = timezone.now() - timedelta(seconds=1)
        self.profile.save()
        game.claim_ore_reward(self.profile)
        run.refresh_from_db()
        self.assertEqual(run.progress, {})
        activate_story(self.profile, run.pk)
        with patch('characters.game_logic.simulate_combat', return_value=game.CombatResult(False, [], 40)):
            game.execute_hunt(self.profile, 'young_scavenger', 'exchange')
        run.refresh_from_db()
        self.assertEqual(run.progress.get('hunt', 0), 0)
        with patch('characters.game_logic.simulate_combat', return_value=game.CombatResult(True, [], 40)):
            game.execute_hunt(self.profile, 'young_scavenger', 'exchange')
        game.start_mining(self.profile, 1)
        self.profile.action_end_time = timezone.now() - timedelta(seconds=1)
        self.profile.save()
        game.claim_ore_reward(self.profile)
        run.refresh_from_db()
        self.assertEqual(run.status, 'ready')
        self.assertTrue(claim_story(self.profile, run.pk))

    def test_travel_gates_wait_clock_and_real_delivery(self):
        quest = self.quest(objectives=[goal('travel', 'rice_fields'), goal('wait', seconds=60), goal('item', self.weapon.pk)])
        run = self.active(quest)
        self.assertFalse(travel_story(self.profile, run.pk, 'travel'))  # Level gate.
        self.profile.level = 2
        self.profile.save()
        self.assertTrue(travel_story(self.profile, run.pk, 'travel'))
        item = OwnedItem.objects.create(owner=self.profile, blueprint=self.weapon, is_equipped=True)
        self.assertFalse(claim_story(self.profile, run.pk))
        item.is_equipped = False
        item.is_market_listed = True
        item.market_price = 1
        item.save()
        with patch('django.utils.timezone.now', return_value=run.activated_at + timedelta(seconds=60)):
            self.assertFalse(claim_story(self.profile, run.pk))
            item.is_market_listed = False
            item.save()
            self.assertTrue(claim_story(self.profile, run.pk))
        self.assertFalse(OwnedItem.objects.filter(pk=item.pk).exists())

    def test_reward_failure_rolls_back_items_money_progress_and_ledger(self):
        quest = self.quest(objectives=[goal('item', self.weapon.pk)])
        run = self.active(quest)
        item = OwnedItem.objects.create(owner=self.profile, blueprint=self.weapon)
        with patch('characters.economy.change_premium', side_effect=RuntimeError('ledger unavailable')):
            with self.assertRaises(RuntimeError):
                claim_story(self.profile, run.pk)
        self.profile.refresh_from_db()
        run.refresh_from_db()
        self.assertEqual(self.profile.ore_balance, 50)
        self.assertEqual(run.status, 'active')
        self.assertTrue(OwnedItem.objects.filter(pk=item.pk).exists())
        self.assertFalse(PremiumEntry.objects.exists())

    def test_camp_level_universe_and_active_slot_are_server_gates(self):
        locked = self.quest(level=2, camp='NEW_CAMP', universe='GOTHIC_II')
        self.assertFalse(accept_story(self.profile, locked.pk))
        locked.universe = 'GOTHIC_I'
        locked.save()
        self.assertFalse(accept_story(self.profile, locked.pk))
        self.profile.level = 2
        self.profile.camp = 'NEW_CAMP'
        self.profile.save()
        self.assertTrue(accept_story(self.profile, locked.pk))
        other = self.quest(key='another')
        self.assertFalse(accept_story(self.profile, other.pk))
        self.assertFalse(activate_story(self.other, self.profile.story_runs.get().pk))

    def test_bot_uses_same_services_to_finish_dialogue_timer_and_delivery(self):
        quest = self.quest(objectives=[goal('talk', options={'help': 'Pomogę'}), goal('travel', 'exchange'), goal('wait', seconds=10), goal('item', self.weapon.pk)])
        self.profile.is_bot = True
        self.profile.camp = 'OLD_CAMP'
        self.profile.guild = 'BARON'
        self.profile.save()
        now = timezone.now()
        for minute in range(12):
            with patch('django.utils.timezone.now', return_value=now + timedelta(minutes=minute)):
                _, success = tick_bot(self.profile)
                self.assertTrue(success)
            if self.profile.story_runs.filter(status='claimed').exists(): break
        run = self.profile.story_runs.get()
        self.assertEqual(run.status, 'claimed')
        self.assertEqual(run.choices, {'talk': 'help'})
        self.assertEqual(PremiumEntry.objects.get().reference, f'story:{run.pk}')

    def test_validation_rejects_cycles_malformed_goals_and_negative_rewards(self):
        quest = self.quest()
        second = self.quest(key='second', prerequisites=['first'])
        quest.prerequisites = ['second']
        with self.assertRaises(ValidationError): validate_definition(quest)
        quest.prerequisites = []
        for objectives, rewards in [([goal('hunt', {})], {}), ([goal('talk', options={})], {}), ([goal('wait', seconds=-1)], {}), ([goal('mine')], {'ore': -10})]:
            quest.objectives, quest.rewards = objectives, rewards
            with self.assertRaises(ValidationError): validate_definition(quest)

    def test_web_auth_escape_and_forged_reward_payload(self):
        self.assertEqual(self.client.get(reverse('story_page')).status_code, 302)
        quest = self.quest(title='<script>bad</script>')
        self.client.force_login(self.profile.user)
        self.assertContains(self.client.get(reverse('story_page')), '&lt;script&gt;')
        self.client.post(reverse('story_page'), {'action': 'accept', 'target': quest.pk, 'ore': 100000})
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.ore_balance, 50)
        self.assertEqual(self.client.post(reverse('story_page'), {'action': 'claim', 'target': 'bad'}).status_code, 404)

    def test_seed_is_repeatable_preserves_edits_and_bot_finishes_real_prologue(self):
        call_command('seed_story', stdout=StringIO())
        intro = StoryQuest.objects.get(key='prologue-arrival')
        intro.description = 'Tekst zarządcy'
        intro.save()
        call_command('seed_story', stdout=StringIO())
        intro.refresh_from_db()
        self.assertEqual(intro.description, 'Tekst zarządcy')
        self.profile.is_bot = True
        self.profile.save()
        now = timezone.now()
        for step in range(120):
            with patch('django.utils.timezone.now', return_value=now + timedelta(minutes=step)):
                _, success = tick_bot(self.profile)
                self.assertTrue(success, step)
            if self.profile.story_runs.filter(status='claimed', quest__key__startswith='prologue-').count() == 3: break
        self.assertEqual(self.profile.story_runs.filter(status='claimed', quest__key__startswith='prologue-').count(), 3)
        self.assertFalse(PremiumEntry.objects.exclude(reference__startswith='story:').exists())

    def test_alternative_predecessors_merge_camp_branches_without_crossing_them(self):
        first = self.quest()
        merge = self.quest(key='merge', any_prerequisites=['first', 'other-camp-ending'])
        self.assertFalse(accept_story(self.profile, merge.pk))
        run = self.active(first)
        choose_story(self.profile, run.pk, 'talk', 'help')
        claim_story(self.profile, run.pk)
        self.assertTrue(accept_story(self.profile, merge.pk))

    def test_wrong_decision_keeps_branch_locked(self):
        first = self.quest()
        branch = self.quest(key='branch', prerequisites=['first'], required_choices={'first': {'talk': 'help'}})
        run = self.active(first)
        choose_story(self.profile, run.pk, 'talk', 'ask')
        claim_story(self.profile, run.pk)
        self.assertFalse(accept_story(self.profile, branch.pk))
