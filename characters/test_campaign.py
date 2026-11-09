from collections import Counter
from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from .models import StoryQuest, StoryRun, PlayerProfile, PremiumEntry, BotDecision, CampaignCompletion
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
        call_command('seed_catalog', stdout=StringIO())
        # Stable IDs exercise two mage branches and all three camps on both databases.
        # Only fixture identity/randomness is controlled, never stats, resources or outcomes.
        import random
        from django.db import connection
        state=random.getstate();self.addCleanup(random.setstate,state);random.seed(19)
        self.assertFalse(PlayerProfile.objects.exists())
        with connection.cursor() as cursor:
            if connection.vendor=='postgresql':
                cursor.execute("SELECT setval(pg_get_serial_sequence('characters_playerprofile','id'),221,true)")
            else:
                cursor.execute("UPDATE sqlite_sequence SET seq=221 WHERE name='characters_playerprofile'")
                if not cursor.rowcount:cursor.execute("INSERT INTO sqlite_sequence(name,seq) VALUES ('characters_playerprofile',221)")
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
                    action, success = tick_bot(bot, force_active=True)
                    self.assertTrue(success, (step, bot.pk, action))
                    actions[action] += 1
                    if bot.story_runs.filter(quest__key='ritual-ready', status='claimed').exists() and CampaignCompletion.objects.filter(profile=bot).exists():
                        completed.add(bot.pk)
            if len(completed) == 3: break
        status = {b.pk: list(b.story_runs.exclude(status='claimed').values('quest__key', 'progress', 'status')) for b in bots}
        self.assertEqual(len(completed), 3, (status, actions, list(PlayerProfile.objects.filter(is_bot=True).values('id','guild','level','strength','mana','current_mana','current_health','life','prepared_magic_id','skill_points')), list(BotDecision.objects.values('profile_id','reason','observation')[:1])))
        for bot in bots:
            bot.refresh_from_db()
            self.assertGreaterEqual(bot.level, 30)
            self.assertEqual(bot.story_runs.filter(status='claimed', quest__camp=bot.camp).count(), 6)
            self.assertEqual(bot.story_runs.filter(status='claimed').exclude(quest__camp__in=['', bot.camp]).count(), 0)
            self.assertLessEqual(bot.inventory.exclude(blueprint__kind="quest",blueprint__tradeable=False).count(), 12)
            self.assertIn(bot.story_runs.filter(status='claimed').count(), (27,28))
            self.assertTrue(hasattr(bot,'campaign_completion'))
        from .release_probe import record_scenario
        record_scenario('trzy-obozy-botow',{'ticks':step+1,'simulated_hours':step/2,'actions':dict(actions),'characters':list(PlayerProfile.objects.filter(pk__in=[b.pk for b in bots]).values('camp','level','experience','ore_balance','premium_balance')),'finishers':sum(hasattr(b,'campaign_completion') for b in bots)})
        # Continue the same earned characters after the finale: no stat/material grants.
        after=Counter()
        for extra in range(60):
            with patch('django.utils.timezone.now',return_value=now+timedelta(minutes=30*(step+extra+1))):
                for bot in bots:
                    action,success=tick_bot(bot, force_active=True)
                    self.assertTrue(success,(extra,bot.pk,action))
                    after[action]+=1
        for bot in bots:
            self.assertTrue(bot.patrols.filter(won=True).exists(),(bot.pk,after))
            self.assertTrue(bot.equipment_work.filter(action='improve').exists(),(bot.pk,after))
            self.assertLessEqual(bot.inventory.exclude(blueprint__kind='quest',blueprint__tradeable=False).count(),12)
        record_scenario('po-finale-dalsze-zycie',{'ticks_per_bot':60,'actions':dict(after),'characters':[{'camp':b.camp,'patrol_wins':b.patrols.filter(won=True).count(),'upgrades':b.equipment_work.filter(action='improve').count()} for b in bots]})
        self.assertFalse(BotDecision.objects.filter(success=False).exists())
        for action in ('story_accept', 'story_start', 'story_claim', 'story_talk', 'story_travel', 'hunt', 'boss', 'mine', 'claim', 'stock'):
            self.assertGreater(actions[action], 0)
        self.assertTrue(PremiumEntry.objects.filter(reference__startswith='story:').exists())

    def test_human_can_play_whole_campaign_via_forms_and_ordinary_game_services(self):
        from . import game_logic as game
        from .models import ItemBluePrint, OwnedItem
        from .world_management import seed_clean_world
        seed_clean_world()
        hero = User.objects.create_user('solo-player').playerprofile
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
                if response.url.startswith('/konto/logowanie/'):
                    # A long simulated campaign can outlive the ordinary 14-day login session.
                    self.client.force_login(hero.user)
                    response = self.client.post('/fabula/', {'action': action, 'target': target, **kwargs})
            self.assertEqual(response.status_code, 302)
            hero.refresh_from_db()
            from .story_gates import missing
            if hero.camp == "NONE" and not missing(hero):
                with advance():
                    self.assertEqual(self.client.post("/", {"camp":"OLD_CAMP"}).status_code,302)
                hero.refresh_from_db()
                self.assertEqual(hero.camp,"OLD_CAMP")
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
            best = ItemBluePrint.objects.filter(merchant=True,kind='weapon',weapon_type__in=['onehand','twohand'],required_strength__lte=hero.strength,required_dexterity__lte=hero.dexterity,min_level__lte=hero.level,min_camp_tier__lte=hero.camp_tier,required_camp__in=['',hero.camp],base_value__gt=0).order_by('-damage').first()
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
                                self.assertTrue(hero.battles.first().won,hero.battles.first().combat_log)
                            else:
                                self.assertTrue(game.execute_boss(hero, goal['target']).won)
                elif kind == 'wait':
                    with advance(): game.refresh_player(hero)
            post('claim', run.pk)
            run.refresh_from_db()
            self.assertEqual(run.status, 'claimed', run.snapshot['key'])
        self.assertTrue(hero.story_runs.filter(quest__key='ritual-ready', status='claimed').exists())
        page = self.client.get('/fabula/')
        self.assertContains(page, 'Osobisty przydział przygotowań zakończony')
        self.assertContains(page, 'Sześć rozdziałów')
        self.assertContains(page, 'Gothicpedia')

        prepare()
        with advance():
            result = game.execute_boss(hero, 'sleeper_sanctum')
        self.assertIsNot(result, False)
        self.assertTrue(result.won)
        self.assertTrue(hasattr(hero,'campaign_completion'))
        with advance():
            self.client.force_login(hero.user)
            self.assertContains(self.client.get('/sala-chwaly/'), 'solo-player')
        hero.refresh_from_db()
        from .release_probe import record_scenario
        record_scenario('gracz-od-zera-do-finalu',{'steps':step,'simulated_hours':step/2,'chapters':6,'claimed_quests':hero.story_runs.filter(status='claimed').count(),'level':hero.level,'experience':hero.experience,'ore':hero.ore_balance,'premium':hero.premium_balance,'completion':hasattr(hero,'campaign_completion')})

        # The same earned human character can spend drops and continue after the ending.
        from uuid import uuid4
        from .models import OwnedItem,FrontierProgress
        weapon=hero.inventory.filter(is_equipped=True,equipped_slot='weapon').first()
        self.assertIsNotNone(weapon)
        with advance():
            response=self.client.get('/ekwipunek/')
            upgrade_key=response.context['request_key']
            response=self.client.post('/ekwipunek/',{'action':'improve','item_id':weapon.pk,'expected_level':0,'request_key':upgrade_key})
        self.assertEqual(response.status_code,302)
        weapon.refresh_from_db();self.assertEqual(weapon.upgrade_level,1)
        with advance():
            key=uuid4()
            response=self.client.post('/warty/',{'depth':1,'request_key':key,'ore':999999})
        self.assertEqual(response.status_code,302)
        self.assertTrue(hero.patrols.get(request_key=key).won)
        self.assertEqual(FrontierProgress.objects.get(profile=hero).unlocked,2)
        record_scenario('gracz-po-finale',{'upgraded_item':weapon.blueprint.name,'upgrade_level':weapon.upgrade_level,'patrol_wins':hero.patrols.filter(won=True).count(),'unlocked':2,'admin_grants':False})
