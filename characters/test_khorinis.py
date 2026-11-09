from collections import Counter
from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from .models import PlayerProfile,StoryQuest,CampGuild,World,ItemBluePrint,OwnedItem,AdventureTemplate,WorldEvent
from .worlds import current_world
from .realms import world_scope
from .character_selection import create_character
from . import game_logic as game

class TwoRealmTests(TestCase):
    def setUp(self):
        from .world_management import seed_clean_world
        seed_clean_world();self.colony=current_world();self.colony.configured=True;self.colony.bot_count=0;self.colony.save()
        call_command('open_khorinis',bots=3,stdout=StringIO())
        self.island=World.objects.get(universe='GOTHIC_II',is_open=True)
        self.user=User.objects.create_user('dwa-swiaty');self.original=self.user.playerprofile
        self.p=create_character(self.user,'Portowy przybysz',self.island.pk)
    def test_both_worlds_have_separate_characters_context_and_safe_old_forms(self):
        self.client.force_login(self.user);self.assertContains(self.client.get('/postacie/'),'Latarnia')
        self.client.post('/postacie/',{'profile':self.p.pk})
        page=self.client.get('/');self.assertEqual(page.context['profile'].pk,self.p.pk)
        self.assertEqual(page.context['server_world'].pk,self.island.pk)
        self.assertContains(page,'Port Khorinis');self.assertNotContains(page,'Zamek Starego Obozu')
        self.assertContains(self.client.get('/fabula/'),'Szlaki zaopatrzenia')
        from django.urls import reverse
        rankings=self.client.get(reverse('rankings_page'))
        self.assertEqual({row[0] for row in rankings.context['camps']},{'CITY_WATCH','FIRE_ORDER','ONAR_MERCS'})
        self.assertNotContains(rankings,'Stary Obóz')
        self.assertEqual(self.client.get('/polowanie/?location=forest').status_code,403)
        self.assertEqual(self.client.get('/polowanie/?location=k2_fields').status_code,200)
        self.assertEqual(current_world().pk,self.colony.pk) # ContextVar reset after response.
        self.client.post('/postacie/',{'profile':self.original.pk})
        self.assertContains(self.client.get('/'),'Zamek Starego Obozu')
        self.assertEqual(self.client.get('/polowanie/?location=k2_fields').status_code,403)
    def test_cross_realm_market_events_story_adventures_and_gear_are_rejected(self):
        bp=ItemBluePrint.objects.filter(source_game='GOTHIC_I',merchant=True).first()
        self.assertFalse(game.buy_item_from_npc(self.p,bp))
        item=OwnedItem.objects.create(owner=self.original,blueprint=bp,is_market_listed=True,market_price=1)
        self.assertFalse(game.buy_item_on_market(self.p,item,1))
        self.assertFalse(game.execute_hunt(self.p,'young_scavenger','forest'))
        self.assertFalse(game.execute_hunt(self.original,'k2_scavenger','k2_fields'))
        from .story_quests import accept_story
        self.assertFalse(accept_story(self.p,StoryQuest.objects.get(key='prologue-arrival').pk))
        from .economy import start_adventure
        self.assertFalse(start_adventure(self.p,AdventureTemplate.objects.get(key='courier').pk))
        self.assertFalse(start_adventure(self.original,AdventureTemplate.objects.get(key='k2-port').pk))
        WorldEvent.objects.create(world=self.island,key='island-only',name='Tylko wyspa',starts_at=timezone.now()-timedelta(hours=1),ends_at=timezone.now()+timedelta(hours=1),ore_percent=200)
        from .world_events import active_events
        with world_scope(self.island):self.assertTrue(active_events().filter(key='island-only').exists())
        self.assertFalse(active_events().filter(key='island-only').exists())
        self.assertEqual(self.p.inventory.count(),0)
    def test_jarkendar_and_postmerge_bosses_are_not_available_even_with_shards(self):
        self.p.premium_balance=100000;self.p.level=100;self.p.save();self.client.force_login(self.user);self.client.post('/postacie/',{'profile':self.p.pk})
        for key in ('jarkendar','raven','ice_dragon','sleeper_sanctum'):
            self.assertFalse(game.execute_boss(self.p,key))
        self.assertEqual(self.client.get('/polowanie/?location=jarkendar').status_code,404)
        from .locations import LOCATIONS
        self.assertFalse(any('jarkendar' in l.key for l in LOCATIONS))
        self.assertFalse(game.choose_camp(self.p,'CITY_WATCH'))
        self.assertFalse(game.choose_camp(self.p,'OLD_CAMP'))
    def test_open_is_idempotent_and_does_not_touch_colony(self):
        before=list(CampGuild.objects.filter(world=self.colony).values())
        call_command('open_khorinis',bots=100,name='Nie nadpisuj',stdout=StringIO())
        self.island.refresh_from_db();self.assertEqual(self.island.bot_count,3);self.assertEqual(self.island.name,'Latarnia — Khorinis')
        self.assertEqual(before,list(CampGuild.objects.filter(world=self.colony).values()))
        self.assertEqual(PlayerProfile.objects.filter(world=self.island,is_bot=True).count(),3)
        self.assertEqual(PlayerProfile.objects.filter(world=self.colony,is_bot=True).count(),0)
    def test_three_factions_finish_story_by_ordinary_bot_actions(self):
        import random
        state=random.getstate();self.addCleanup(random.setstate,state);random.seed(4926)
        from .bots import tick_bot
        bots=list(PlayerProfile.objects.filter(world=self.island,is_bot=True).order_by('pk'))
        now=timezone.now();done=set();actions=Counter()
        for step in range(700):
            with patch('django.utils.timezone.now',return_value=now+timedelta(minutes=30*step)):
                for bot in bots:
                    if bot.pk in done:continue
                    action,ok=tick_bot(bot,force_active=True);self.assertTrue(ok,(step,bot.pk,action));actions[action]+=1
                    if bot.story_runs.filter(status='claimed',snapshot__key='k2-supply-8').exists():done.add(bot.pk)
            if len(done)==3:break
        # The same earned characters keep playing after their pre-merge story.
        for extra in range(80):
            with patch('django.utils.timezone.now',return_value=now+timedelta(minutes=30*(step+extra+1))):
                for bot in bots:
                    action,ok=tick_bot(bot,force_active=True);self.assertTrue(ok,(extra,bot.pk,action));actions[action]+=1
        status=list(PlayerProfile.objects.filter(pk__in=[b.pk for b in bots]).values('id','camp','guild','level','strength','mana','ore_balance'))
        self.assertEqual(len(done),3,(status,actions,{b.pk:list(b.story_runs.exclude(status='claimed').values('snapshot__key','progress')) for b in bots}))
        self.assertEqual({p['camp'] for p in status},{'CITY_WATCH','FIRE_ORDER','ONAR_MERCS'})
        mage=next(b for b in bots if PlayerProfile.objects.get(pk=b.pk).camp=='FIRE_ORDER')
        self.assertTrue(mage.battles.filter(combat_details__casts__gt=0).exists())
        for bot in bots:
            bot.refresh_from_db();self.assertEqual(bot.camp_tier,3)
            self.assertEqual(bot.story_runs.filter(status='claimed').count(),17)
            self.assertFalse(bot.story_runs.exclude(snapshot__universe='GOTHIC_II').exists())
        self.assertEqual(current_world().pk,self.colony.pk)
        from .release_probe import record_scenario
        record_scenario('khorinis-trzy-frakcje',{'ticks':step+1,'quests_each':17,'actions':dict(actions),'characters':status,'ordinary_services_without_grants':True})

    def test_human_completes_island_campaign_using_forms_without_grants(self):
        from .story_quests import available
        from .locations import LOCATIONS
        self.client.force_login(self.user);self.client.post('/postacie/',{'profile':self.p.pk})
        now=timezone.now();step=0
        def advance():
            nonlocal step
            step+=1
            return patch('django.utils.timezone.now',return_value=now+timedelta(minutes=30*step))
        def post(action,target,**kwargs):
            with advance():
                response=self.client.post('/fabula/',{'action':action,'target':target,**kwargs})
                if response.url.startswith('/konto/logowanie/'):
                    self.client.force_login(self.user);self.client.post('/postacie/',{'profile':self.p.pk})
                    response=self.client.post('/fabula/',{'action':action,'target':target,**kwargs})
                self.assertEqual(response.status_code,302)
            self.p.refresh_from_db()
            if self.p.camp=='NONE' and self.p.story_runs.filter(snapshot__key='k2-citizenship',status='claimed').exists():
                with advance():self.client.post('/',{'camp':'CITY_WATCH'})
                self.p.refresh_from_db();self.assertEqual(self.p.camp,'CITY_WATCH')
        def mine():
            with advance():self.assertTrue(game.start_mining(self.p,15))
            with advance():self.assertTrue(game.claim_ore_reward(self.p))
        def prepare():
            with advance():game.refresh_player(self.p)
            for _ in range(self.p.skill_points):
                if self.p.ore_balance<30:mine()
                with advance():self.assertTrue(game.train_attribute(self.p,'strength'))
            bp=ItemBluePrint.objects.filter(source_game='GOTHIC_II',kind='weapon',weapon_type='onehand',min_level__lte=self.p.level,required_strength__lte=self.p.strength).order_by('-damage').first()
            equipped=self.p.inventory.filter(is_equipped=True,equipped_slot='weapon').first()
            if not equipped or equipped.blueprint.damage<bp.damage:
                while self.p.ore_balance<bp.base_value:mine()
                with advance():self.assertTrue(game.buy_item_from_npc(self.p,bp))
                with advance():self.assertTrue(game.equip_item(self.p,self.p.inventory.filter(blueprint=bp,is_equipped=False).first()))
        for _ in range(17):
            self.p.refresh_from_db()
            quest=next((q for q in StoryQuest.objects.filter(universe='GOTHIC_II') if not self.p.story_runs.filter(quest=q).exists() and available(self.p,q)),None)
            self.assertIsNotNone(quest,(self.p.level,list(self.p.story_runs.values_list('snapshot__key',flat=True))))
            post('accept',quest.pk);run=self.p.story_runs.get(quest=quest);post('start',run.pk)
            for goal in run.snapshot['objectives']:
                kind=goal['kind']
                if kind=='talk':post('talk',run.pk,goal=goal['id'],option=next(iter(goal['options'])))
                elif kind=='travel':post('travel',run.pk,goal=goal['id'])
                elif kind=='mine':
                    for _ in range(goal.get('count',1)):mine()
                elif kind=='train':
                    with advance():self.assertTrue(game.train_attribute(self.p,goal['target']))
                elif kind in {'hunt','boss'}:
                    prepare()
                    for _ in range(goal.get('count',1)):
                        with advance():
                            if kind=='hunt':
                                loc=next(l for l in LOCATIONS if l.accessible(self.p) and goal['target'] in l.monsters)
                                self.assertTrue(game.execute_hunt(self.p,goal['target'],loc.key))
                                self.assertTrue(self.p.battles.first().won)
                            else:self.assertTrue(game.execute_boss(self.p,goal['target']).won)
                elif kind=='wait':
                    with advance():game.refresh_player(self.p)
            post('claim',run.pk);run.refresh_from_db();self.assertEqual(run.status,'claimed',run.snapshot['key'])
        self.assertTrue(self.p.story_runs.filter(snapshot__key='k2-supply-8',status='claimed').exists())
        self.assertFalse(self.p.campaigncompletion_set.exists() if hasattr(self.p,'campaigncompletion_set') else hasattr(self.p,'campaign_completion'))
        self.assertEqual(World.objects.filter(is_open=True,universe='GOTHIC_II').count(),1)
        from .release_probe import record_scenario
        record_scenario('khorinis-gracz-od-zera',{'steps':step,'quests':17,'level':self.p.level,'ore':self.p.ore_balance,'experience':self.p.experience,'ordinary_forms_without_grants':True})

    def test_scheduler_has_distinct_leases_and_one_shared_population_queue(self):
        from contextlib import ExitStack
        from .realm_scheduler import ParallelRealms
        from .scheduler_lease import SchedulerGuard,LeaseLost
        from .health import ready
        from django.test import RequestFactory
        from .bots import tick_bot
        self.island.bot_personality_cycles=False;self.island.save()
        with ExitStack() as cleanup,SchedulerGuard(self.colony) as primary:
            realms=ParallelRealms();ids=realms.sync(primary,cleanup)
            self.assertEqual(len(ids),3)
            self.assertEqual(ready(RequestFactory().get('/health/ready/')).status_code,200)
            self.assertEqual(set(realms.guards),{self.colony.pk,self.island.pk})
            with self.assertRaises(LeaseLost):SchedulerGuard(self.island).acquire()
            bot=PlayerProfile.objects.get(pk=ids[0])
            with self.assertRaises(LeaseLost):tick_bot(bot,lease=primary,force_active=True)
            action,ok=tick_bot(bot,lease=realms.for_profile(bot),force_active=True);self.assertTrue(ok,action)
            realms.sync(primary,cleanup) # Must not release the primary lease on refresh.
            with primary.work():pass
        self.assertEqual(ready(RequestFactory().get('/health/ready/')).status_code,503)

    def test_manager_selects_world_without_changing_played_character(self):
        self.user.is_superuser=True;self.user.is_staff=True;self.user.save()
        self.client.force_login(self.user)
        response=self.client.get('/zarzadca/swiat/reset/?server='+str(self.island.pk))
        self.assertEqual(response.context['world'].pk,self.island.pk)
        self.assertEqual(self.user.characters.count(),2) # Manager GET must not create an implicit character.
        self.assertEqual(response.context['server_world'].pk,self.island.pk)
        self.assertEqual(self.client.get('/').context['profile'].pk,self.original.pk)
        response=self.client.post('/zarzadca/swiat/reset/?server='+str(self.island.pk),{'action':'configure','name':'Latarnia testowa','bot_count':4,'bot_personality_cycles':'on'})
        self.assertEqual(response.status_code,302);self.island.refresh_from_db();self.colony.refresh_from_db()
        self.assertEqual(self.island.bot_count,4);self.assertEqual(self.colony.bot_count,0)
        self.assertEqual(PlayerProfile.objects.filter(world=self.island,is_bot=True).count(),4)
        manager=self.client.get('/zarzadca/?server='+str(self.island.pk)+'&profile='+str(self.p.pk))
        self.assertContains(manager,'name="server" value="'+str(self.island.pk)+'"')
        response=self.client.post('/zarzadca/?server='+str(self.island.pk),{'action':'restore','profile':self.p.pk})
        self.assertIn('server='+str(self.island.pk),response.url)
        self.assertEqual(self.client.get(response.url).status_code,200)
