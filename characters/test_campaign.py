from collections import Counter
from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from .models import StoryQuest, StoryRun, PlayerProfile, PremiumEntry, BotDecision
from .story_quests import validate_definition, available
from .bots import tick_bot
from .gothic_campaign import campaign_definitions


class CampaignTests(TestCase):
    def setUp(self):
        call_command('seed_story', stdout=StringIO())

    def test_complete_catalog_has_38_new_quests_and_no_invalid_references(self):
        quests = list(StoryQuest.objects.all())
        self.assertEqual(len(quests), 41)
        keys = {q.key for q in quests}
        kinds = Counter()
        for quest in quests:
            quest.full_clean()
            self.assertTrue(set(quest.prerequisites + quest.any_prerequisites) <= keys)
            for g in quest.objectives:
                kinds[g['kind']] += 1
            if quest.key.startswith(('old-', 'new-', 'swamp-')):
                self.assertTrue(quest.camp)
        self.assertEqual(len({q.chapter for q in quests}), 6)
        for kind in ('mine', 'hunt', 'boss', 'travel', 'talk', 'wait', 'item', 'train'):
            self.assertGreater(kinds[kind], 0)
        for camp in ('OLD_CAMP', 'NEW_CAMP', 'SWAMP_CAMP'):
            self.assertEqual(sum(q.camp == camp for q in quests), 6)

    def test_seeding_does_not_reset_admin_rewards_or_versions(self):
        quest = StoryQuest.objects.get(key='xardas-warning')
        quest.rewards = {'ore': 17}
        quest.version = 7
        quest.save()
        call_command('seed_story', stdout=StringIO())
        quest.refresh_from_db()
        self.assertEqual((quest.rewards, quest.version), ({'ore': 17}, 7))
        self.assertEqual(StoryQuest.objects.count(), 41)

    def test_every_camp_bot_can_finish_from_new_character_without_runtime_grants(self):
        call_command('seed_equipment', stdout=StringIO())
        # Simulated elapsed time grants only the ordinary capped resource recovery.
        # No combat mocks, forced progress, stat/XP grants or injected quest outcomes.
        call_command('run_bots', create=3, create_only=True, stdout=StringIO())
        bots = list(PlayerProfile.objects.filter(is_bot=True).order_by('pk'))
        now = timezone.now()
        completed = set()
        actions = Counter()
        for step in range(700):
            with patch('django.utils.timezone.now', return_value=now + timedelta(minutes=30*step)):
                for bot in bots:
                    if bot.pk in completed: continue
                    action, success = tick_bot(bot)
                    self.assertTrue(success, (step, bot.pk, action))
                    actions[action] += 1
                    if bot.story_runs.filter(quest__key='ritual-ready', status='claimed').exists():
                        completed.add(bot.pk)
            if len(completed) == 3: break
        status = {b.pk: list(b.story_runs.exclude(status='claimed').values('quest__key', 'progress', 'status')) for b in bots}
        self.assertEqual(len(completed), 3, (status, actions))
        for bot in bots:
            bot.refresh_from_db()
            self.assertGreaterEqual(bot.level, 30)
            self.assertEqual(bot.story_runs.filter(status='claimed', quest__camp=bot.camp).count(), 6)
            self.assertEqual(bot.story_runs.filter(status='claimed').exclude(quest__camp__in=['', bot.camp]).count(), 0)
            self.assertLessEqual(bot.inventory.count(), 6)
            self.assertEqual(bot.story_runs.filter(status='claimed').count(), 27)
        self.assertFalse(BotDecision.objects.filter(success=False).exists())
        for action in ('story_accept', 'story_start', 'story_claim', 'story_talk', 'story_travel', 'hunt', 'boss', 'mine', 'claim', 'stock'):
            self.assertGreater(actions[action], 0)
        self.assertTrue(PremiumEntry.objects.filter(reference__startswith='story:').exists())

    def test_human_can_play_whole_campaign_via_forms_and_ordinary_game_services(self):
        from . import game_logic as game
        from .models import ItemBluePrint, OwnedItem
        hero = User.objects.create_user('solo-player').playerprofile
        game.choose_camp(hero, 'OLD_CAMP')
        self.client.force_login(hero.user)
        now = timezone.now()
        step = 0
        def advance():
            nonlocal step
            step += 1
            return patch('django.utils.timezone.now', return_value=now + timedelta(minutes=30*step))
        def post(action, target, **kwargs):
            with advance():
                response = self.client.post('/fabula/', {'action': action, 'target': target, **kwargs})
            self.assertEqual(response.status_code, 302)
        def mining_shift():
            with advance(): self.assertTrue(game.start_mining(hero, 15))
            with advance(): self.assertTrue(game.claim_ore_reward(hero))
        def prepare():
            with advance(): game.refresh_player(hero)
            # Spend only the points and ore actually earned by this character.
            hero.refresh_from_db()
            for _ in range(hero.skill_points):
                if hero.ore_balance < 30: mining_shift()
                with advance(): self.assertTrue(game.train_attribute(hero, 'strength'))
            best = ItemBluePrint.objects.filter(required_strength__lte=hero.strength, base_value__gt=0).order_by('-damage').first()
            equipped = hero.inventory.filter(is_equipped=True).select_related('blueprint').first()
            if not equipped or equipped.blueprint.damage < best.damage:
                while hero.ore_balance < best.base_value: mining_shift()
                with advance(): self.assertTrue(game.buy_item_from_npc(hero, best))
                with advance(): self.assertTrue(game.equip_item(hero, hero.inventory.filter(blueprint=best, is_equipped=False).first()))
        for _ in range(27):
            hero.refresh_from_db()
            quest = next((q for q in StoryQuest.objects.all() if not hero.story_runs.filter(quest=q).exists() and available(hero, q)), None)
            self.assertIsNotNone(quest)
            post('accept', quest.pk)
            run = hero.story_runs.get(quest=quest)
            post('start', run.pk)
            for goal in run.snapshot['objectives']:
                kind = goal['kind']
                if kind == 'talk': post('talk', run.pk, goal=goal['id'], option=next(iter(goal['options'])))
                elif kind == 'travel': post('travel', run.pk, goal=goal['id'])
                elif kind == 'mine':
                    for _ in range(goal.get('count', 1)): mining_shift()
                elif kind == 'item':
                    blueprint = ItemBluePrint.objects.get(pk=goal['target'])
                    for _ in range(goal.get('count', 1)):
                        with advance(): self.assertTrue(game.buy_item_from_npc(hero, blueprint))
                elif kind == 'train':
                    with advance(): self.assertTrue(game.train_attribute(hero, goal['target']))
                elif kind in ('hunt', 'boss'):
                    from .locations import LOCATIONS
                    prepare()
                    for _ in range(goal.get('count', 1)):
                        with advance():
                            if kind == 'hunt':
                                location = next(loc for loc in LOCATIONS if loc.accessible(hero) and goal['target'] in loc.monsters)
                                self.assertIsNot(game.execute_hunt(hero, goal['target'], location.key), False)
                            else:
                                self.assertTrue(game.execute_boss(hero, goal['target']).won)
                elif kind == 'wait':
                    with advance(): game.refresh_player(hero)
            post('claim', run.pk)
            run.refresh_from_db()
            self.assertEqual(run.status, 'claimed', run.snapshot['key'])
        self.assertTrue(hero.story_runs.filter(quest__key='ritual-ready', status='claimed').exists())
        page = self.client.get('/fabula/')
        self.assertContains(page, 'Przygotowania do finału zakończone')
        self.assertContains(page, 'Sześć rozdziałów')
        self.assertContains(page, 'Gothicpedia')
