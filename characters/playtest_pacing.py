"""Opt-in wall-clock campaign model: earned resources, ten seconds per action.

No production writes: invoked by Django's test runner on its isolated database.
The clock only advances for actions, actual timers, recovery and session breaks.
"""
from collections import Counter
from datetime import datetime,timedelta
from io import StringIO
import random
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from .barrier import region,source_games
from django.test import TestCase
from . import game_logic as game
from .models import StoryQuest,ItemBluePrint,World,AdventureTemplate
from .world_management import seed_clean_world
from .worlds import current_world
from .character_selection import create_character
from .story_quests import available
from .locations import LOCATIONS
from .equipment import allowed
from .release_probe import record_scenario
from .world_clock import POLISH_TIME


class CampaignPacingTests(TestCase):
    def test_colony_continuous(self):self.play('GOTHIC_I',None)
    def test_island_continuous(self):self.play('GOTHIC_II',None)
    def test_colony_one_hour_daily(self):self.play('GOTHIC_I',60)
    def test_island_one_hour_daily(self):self.play('GOTHIC_II',60)
    def test_colony_armor_and_earned_shop(self):self.play('GOTHIC_I',None,support=True)
    def test_island_armor_and_earned_shop(self):self.play('GOTHIC_II',None,support=True)

    def test_colony_contract_income(self):self.play('GOTHIC_I',None,support=True,income_first=True)
    def test_island_contract_income(self):self.play('GOTHIC_II',None,support=True,income_first=True)

    def play(self,universe,session_minutes,*,support=False,income_first=False,joined_start=False,after_campaign=None):
        with patch('django.utils.timezone.now',return_value=datetime(2026,11,11,9,tzinfo=POLISH_TIME)):
            seed_clean_world();world=current_world();world.configured=True;world.bot_count=0;world.save()
            if universe=='GOTHIC_II':
                call_command('open_khorinis',bots=0,stdout=StringIO());world=World.objects.get(universe=universe)
            if joined_start:
                from uuid import uuid4
                call_command('open_khorinis',bots=0,stdout=StringIO())
                World.objects.filter(is_current=True).update(configured=True)
                World.objects.filter(status='active').update(union_key=uuid4())
                from .post_barrier import seed
                seed()
        state=random.getstate();self.addCleanup(random.setstate,state);random.seed(111126)
        start=datetime(2026,11,11,9,tzinfo=POLISH_TIME);now=start;session_start=start
        event_days=set()
        def calendar():
            if after_campaign and now.date() not in event_days:
                from .realms import world_scope
                from .world_events import ensure_world_events
                for realm in World.objects.filter(status='active'):
                    with world_scope(realm):ensure_world_events(now)
                event_days.add(now.date())
        actions=Counter();active_seconds=0;recovery_seconds=0;timed_seconds=0;offline_seconds=0
        def advance(seconds,kind='action'):
            nonlocal now,session_start,active_seconds,recovery_seconds,timed_seconds,offline_seconds
            if session_minutes and now+timedelta(seconds=seconds)>session_start+timedelta(minutes=session_minutes):
                next_start=(session_start+timedelta(days=1)).replace(hour=9,minute=0,second=0)
                if kind!='action':
                    remaining=max(0,(session_start+timedelta(minutes=session_minutes)-now).total_seconds())
                    if kind=='recovery':recovery_seconds+=remaining
                    else:timed_seconds+=remaining
                    offline_seconds+=(next_start-now).total_seconds()-remaining;now=next_start;session_start=now
                    calendar();return
                offline_seconds+=(next_start-now).total_seconds();now=next_start;session_start=now
            now+=timedelta(seconds=seconds)
            calendar()
            if kind=='action':active_seconds+=seconds
            elif kind=='recovery':recovery_seconds+=seconds
            else:timed_seconds+=seconds
        with patch('django.utils.timezone.now',side_effect=lambda:now):
            calendar()
            user=User.objects.create_user('pacing-player');hero=create_character(user,'Nowy mieszkaniec',current_world().pk if joined_start else world.pk,start_region=world.pk if joined_start else None)
            self.client.force_login(user);self.client.post('/postacie/',{'profile':hero.pk})
            def resupply():
                if not support:return
                from .models import StoreProduct
                from .economy import purchase_product
                from .itemshop_rules import helpful
                from .economic_ledger import refills_remaining
                from uuid import uuid4
                for _ in range(20):
                    hero.refresh_from_db()
                    product=next((q for q in StoreProduct.objects.filter(enabled=True,kind__in=['health','energy']).order_by('price','pk') if helpful(hero,q,refills_remaining(hero)) and ((q.kind=='health' and hero.max_health-hero.current_health>=q.effect) or (q.kind=='energy' and hero.current_energy<15))),None)
                    if not product:return
                    advance(10);self.assertTrue(purchase_product(hero,product.pk,uuid4()));actions['earned_shop_'+product.kind]+=1
            def do(label,fn):
                for _ in range(300):
                    advance(10);hero.refresh_from_db();game.refresh_player(hero)
                    resupply()
                    result=fn();actions[label]+=1
                    if result is not False:return result
                    advance(60,'recovery')
                self.fail((label,hero.level,hero.current_energy,hero.current_health,hero.ore_balance))
            def post(action,target,**kwargs):
                response=do('story_'+action,lambda:self.client.post('/fabula/',{'action':action,'target':target,**kwargs}))
                if response.url.startswith('/konto/logowanie/'):
                    self.client.force_login(user);self.client.post('/postacie/',{'profile':hero.pk})
                    response=self.client.post('/fabula/',{'action':action,'target':target,**kwargs})
                self.assertEqual(response.status_code,302)
                hero.refresh_from_db()
            def mine():
                do('mine',lambda:game.start_mining(hero,15));advance(15,'timer');do('mine_claim',lambda:game.claim_ore_reward(hero))
            def funds(amount):
                for _ in range(2000):
                    hero.refresh_from_db()
                    if hero.ore_balance>=amount:return
                    if income_first:
                        from .economy import start_adventure,claim_adventure
                        template=AdventureTemplate.objects.filter(universe=region(hero).universe,enabled=True,level__lte=hero.level).order_by('-ore_reward','duration_seconds').first()
                        run=do('income_adventure',lambda:start_adventure(hero,template.pk))
                        advance(max(0,int((run.ends_at-now).total_seconds())),'timer')
                        do('income_claim',lambda:claim_adventure(hero,run.pk))
                    else:mine()
                self.fail('Income budget exceeded')
            def prepare():
                hero.refresh_from_db()
                while hero.skill_points:
                    count=min(hero.skill_points,10);funds(hero.training_cost*count)
                    do('train_strength',lambda:game.train_attribute(hero,'strength',count));hero.refresh_from_db()
                choices=ItemBluePrint.objects.filter(source_game__in=source_games(hero),merchant=True,kind='weapon',weapon_type='onehand',base_value__lte=max(100,hero.level*80),required_strength__lte=hero.strength,required_dexterity__lte=hero.dexterity).order_by('-damage','base_value','pk')
                bp=next((b for b in choices if allowed(hero,b)),None);self.assertIsNotNone(bp)
                equipped=hero.inventory.filter(is_equipped=True,equipped_slot='weapon').first()
                if not equipped or equipped.effective_stats['damage']<bp.damage:
                    owned=hero.inventory.filter(blueprint=bp,is_equipped=False,is_market_listed=False).first()
                    if not owned:
                        funds(bp.base_value);do('buy_weapon',lambda:game.buy_item_from_npc(hero,bp));owned=hero.inventory.filter(blueprint=bp,is_equipped=False).first()
                    do('equip_weapon',lambda:game.equip_item(hero,owned))
                if support:
                    armor=next((b for b in ItemBluePrint.objects.filter(source_game__in=source_games(hero),merchant=True,kind='armor',base_value__lte=max(100,hero.level*80),required_strength__lte=hero.strength,required_dexterity__lte=hero.dexterity).order_by('-weapon_prot','base_value','pk') if allowed(hero,b)),None)
                    worn=hero.inventory.filter(is_equipped=True,equipped_slot='armor').first()
                    if armor and (not worn or worn.effective_stats['weapon_prot']<armor.weapon_prot):
                        funds(armor.base_value);do('buy_armor',lambda:game.buy_item_from_npc(hero,armor))
                        owned=hero.inventory.filter(blueprint=armor,is_equipped=False).first();do('equip_armor',lambda:game.equip_item(hero,owned))
                    resupply()
                # Wait only for missing health, rather than inserting a half hour per click.
                hero.refresh_from_db()
                if hero.current_health<hero.max_health:advance((hero.max_health-hero.current_health)*60,'recovery')
            def grind_level():
                template=AdventureTemplate.objects.filter(universe=region(hero).universe,enabled=True,level__lte=hero.level).order_by('-experience_reward').first()
                run=do('adventure_start',lambda:__import__('characters.economy',fromlist=['start_adventure']).start_adventure(hero,template.pk))
                advance(max(0,int((run.ends_at-now).total_seconds())),'timer')
                do('adventure_claim',lambda:__import__('characters.economy',fromlist=['claim_adventure']).claim_adventure(hero,run.pk))
            count=17 if universe=='GOTHIC_II' else 27
            for _ in range(count):
                for _attempt in range(500):
                    hero.refresh_from_db()
                    quest=next((q for q in StoryQuest.objects.filter(universe=universe).order_by('pk') if not hero.story_runs.filter(quest=q).exists() and available(hero,q)),None)
                    if quest:break
                    grind_level()
                self.assertIsNotNone(quest)
                post('accept',quest.pk);run=hero.story_runs.get(quest=quest)
                do('story_energy',lambda:hero.current_energy>=run.snapshot['energy_cost'])
                post('start',run.pk);run.refresh_from_db();self.assertIsNotNone(run.activated_at,quest.key)
                for goal in run.snapshot['objectives']:
                    kind=goal['kind']
                    if kind=='talk':post('talk',run.pk,goal=goal['id'],option=next(iter(goal['options'])))
                    elif kind=='travel':
                        do('travel_energy',lambda:hero.current_energy>=2)
                        post('travel',run.pk,goal=goal['id'])
                    elif kind=='mine':
                        for _ in range(goal.get('count',1)):mine()
                    elif kind=='item':
                        bp=ItemBluePrint.objects.get(pk=goal['target']);funds(bp.base_value*goal.get('count',1))
                        for _ in range(goal.get('count',1)):do('buy_delivery',lambda:game.buy_item_from_npc(hero,bp))
                    elif kind=='train':
                        funds(hero.training_cost);do('train_goal',lambda:game.train_attribute(hero,goal['target']))
                    elif kind in {'hunt','boss'}:
                        prepare()
                        for _ in range(goal.get('count',1)):
                            if kind=='hunt':
                                loc=next(l for l in LOCATIONS if l.accessible(hero) and goal['target'] in l.monsters)
                                do('hunt',lambda:game.execute_hunt(hero,goal['target'],loc.key));self.assertTrue(hero.battles.first().won)
                            else:self.assertTrue(do('boss',lambda:game.execute_boss(hero,goal['target'])).won)
                    elif kind=='wait':
                        advance(max(0,int((run.activated_at+timedelta(seconds=goal['seconds'])-now).total_seconds())),'timer')
                post('claim',run.pk);run.refresh_from_db();self.assertEqual(run.status,'claimed',run.snapshot['key'])
                if hero.camp=='NONE':
                    from .story_gates import missing
                    if not missing(hero):do('join_camp',lambda:game.choose_camp(hero,'CITY_WATCH' if universe=='GOTHIC_II' else 'OLD_CAMP'))
            if universe=='GOTHIC_I':
                prepare();self.assertTrue(do('personal_finale',lambda:game.execute_boss(hero,'sleeper_sanctum')).won)
            hero.refresh_from_db()
            if after_campaign:after_campaign(hero,{'prepare':prepare,'funds':funds,'grind_level':grind_level,'advance':advance,'do':do,'now':lambda:now,'start':start})
            record_scenario('tempo-kampanii-i-kontynuacji' if after_campaign else 'tempo-kampanii',{'universe':universe,'session_minutes':session_minutes,'armor_and_earned_shop':support,'income_first':income_first,'action_seconds':10,'seed':111126,'elapsed_hours':round((now-start).total_seconds()/3600,2),'active_minutes':round(active_seconds/60,1),'recovery_minutes':round(recovery_seconds/60,1),'timers_minutes':round(timed_seconds/60,1),'offline_hours':round(offline_seconds/3600,2),'calendar_days':(now.date()-start.date()).days+1,'level':hero.level,'strength':hero.strength,'quests':hero.story_runs.filter(status='claimed').count(),'ore':hero.ore_balance,'shards':hero.premium_balance,'actions':dict(actions),'defeats':hero.battles.filter(won=False).count(),'admin_grants':False,'limits':['Znająca cele strategia wojownika; nie pomiar zachowania człowieka.','Brak konkurencji rynku i botów; sprzęt od NPC, opcjonalnie itemshop wyłącznie za zarobione odłamki.','Odpoczynek do pełnego zdrowia jest celowo zachowawczy; pozostałe akcje co 10 sekund, także nieudane próby.','Budżet pojedynczego sprzętu: max(100, poziom × 80) rudy. Bez awansów rang i handlu łupami.','Koniec aktualnej kampanii, nie pełnego G2 NK, kolekcji łupów ani rozwoju wspólnoty.']})
