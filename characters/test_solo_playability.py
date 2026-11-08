from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from uuid import uuid4
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from . import game_logic as game
from .models import ItemBluePrint,OwnedItem,StoryQuest,StoryRun,TavernTopic,BotDecision,CampaignCompletion,BossAttempt
from .equipment import add_item
from .merchant_browse import merchant_context
from .player_journey import journey
from .combat_preparation import hunt_preparation


class MasteryTests(TestCase):
    def setUp(self):
        self.p=User.objects.create_user('learner').playerprofile
        self.p.ore_balance=20000;self.p.skill_points=500;self.p.save()
    def test_four_skills_use_real_points_and_money_and_enforce_cap(self):
        for field in game.WEAPON_SKILLS:
            before=(self.p.skill_points,self.p.ore_balance)
            self.assertTrue(game.train_attribute(self.p,field,10))
            self.assertEqual(getattr(self.p,field),10)
            self.assertEqual((self.p.skill_points,self.p.ore_balance),(before[0]-10,before[1]-100))
            setattr(self.p,field,95);self.p.save()
            before=(self.p.skill_points,self.p.ore_balance)
            self.assertFalse(game.train_attribute(self.p,field,10))
            self.assertEqual((self.p.skill_points,self.p.ore_balance),before)
            self.assertTrue(game.train_attribute(self.p,field,5))
            self.assertFalse(game.train_attribute(self.p,field,1))
    def test_bad_fields_counts_and_shortages_do_not_spend(self):
        for field,count in [('ore_balance',1),('onehand_skill',0),('bow_skill',11),('mana',True)]:
            before=(self.p.skill_points,self.p.ore_balance)
            self.assertFalse(game.train_attribute(self.p,field,count))
            self.assertEqual((self.p.skill_points,self.p.ore_balance),before)
        self.p.ore_balance=9;self.p.save()
        self.assertFalse(game.train_attribute(self.p,'bow_skill',1))
        self.p.ore_balance=100;self.p.skill_points=0;self.p.save()
        self.assertFalse(game.train_attribute(self.p,'bow_skill',1))
    def test_forms_and_stale_objects_use_current_resources(self):
        self.client.force_login(self.p.user)
        self.assertContains(self.client.get('/trening/'),'Władanie bronią')
        self.client.post('/trening/',{'attribute':'bow_skill','count':10,'skill_points':999999})
        self.p.refresh_from_db();self.assertEqual(self.p.bow_skill,10)
        self.assertEqual(self.p.skill_points,490)
        self.p.bow_skill=99;self.p.save()
        self.client.post('/trening/',{'attribute':'bow_skill','count':10})
        self.p.refresh_from_db();self.assertEqual(self.p.bow_skill,99)
    def test_veteran_bot_can_learn_without_new_character_grants(self):
        from .bots import tick_bot
        self.p.is_bot=True;self.p.bot_turn=7;self.p.level=30;self.p.strength=300;self.p.camp='OLD_CAMP';self.p.guild='BARON';self.p.save()
        blade=ItemBluePrint.objects.create(name='Oręż weterana',damage=50,merchant=False)
        game.equip_item(self.p,add_item(self.p,blade))
        attempt=BossAttempt.objects.create(profile=self.p,boss_key='sleeper_sanctum',won=True)
        CampaignCompletion.objects.create(profile=self.p,battle=attempt)
        self.assertEqual(tick_bot(self.p),('train',True))
        self.p.refresh_from_db();self.assertEqual(self.p.onehand_skill,1)

    def test_new_level_has_one_reward_notice_without_regranting_points(self):
        self.p.experience=500;self.p.save()
        self.assertTrue(game.check_level_up(self.p))
        points=self.p.skill_points
        self.assertFalse(game.check_level_up(self.p))
        self.assertEqual(self.p.skill_points,points)
        self.assertEqual(self.p.notices.filter(key='level:1').count(),1)
        self.assertIn('+10 PN',self.p.notices.get(key='level:1').title)


class MerchantUsabilityTests(TestCase):
    def setUp(self):
        self.p=User.objects.create_user('shopper').playerprofile
        self.client.force_login(self.p.user)
        self.blade=ItemBluePrint.objects.create(name='Miecz na początek',damage=12,base_value=20,required_strength=10)
        self.bow=ItemBluePrint.objects.create(name='Łuk dla myśliwego',kind='weapon',weapon_type='bow',base_value=30,required_dexterity=15)
    def test_affordable_usable_weapon_filter_finds_first_sword(self):
        for i in range(40):ItemBluePrint.objects.create(name=f'Zapas {i}',kind='consumable',base_value=1)
        context=merchant_context(self.p,{'kind':'weapon','affordable':'1','usable':'1'})
        self.assertEqual([i.pk for i in context['shop_items']],[self.blade.pk])
        self.assertContains(self.client.get('/sklep/',{'kind':'weapon','affordable':'1','usable':'1'}),'Miecz na początek')
    def test_filters_and_both_pages_preserve_context(self):
        for i in range(30):
            bp=ItemBluePrint.objects.create(name=f'Miecz {i}',base_value=10)
            OwnedItem.objects.create(owner=self.p,blueprint=bp)
        context=merchant_context(self.p,{'q':'Miecz','kind':'weapon','page':'2','bag_page':'2'})
        self.assertEqual(context['shop_items'].number,2)
        self.assertEqual(context['player_inventory'].number,2)
        self.assertIn('q=Miecz',context['stock_pager']['previous_url'])
        self.assertIn('bag_page=2',context['stock_pager']['previous_url'])
        context=merchant_context(self.p,{'weapon':'bow','kind':'wrong','page':'bad'})
        self.assertEqual([i.pk for i in context['shop_items']],[self.bow.pk])
    def test_protected_and_prepared_stock_not_offered_for_sale(self):
        one=add_item(self.p,self.blade);one.is_protected=True;one.save()
        two=add_item(self.p,self.bow);self.p.prepared_magic=two;self.p.save()
        self.assertEqual(merchant_context(self.p,{})['player_inventory'].paginator.count,0)
    def test_purchase_preserves_filters_and_service_still_checks_money(self):
        response=self.client.post('/sklep/?kind=weapon&q=Miecz',{'action':'buy','buy_item_id':self.blade.pk})
        self.assertEqual(response.url,'/sklep/?kind=weapon&q=Miecz')
        self.p.refresh_from_db();self.assertEqual(self.p.ore_balance,30)
        self.client.post('/sklep/',{'action':'buy','buy_item_id':self.blade.pk})
        before=self.p.ore_balance;self.p.refresh_from_db()
        self.assertEqual(self.p.ore_balance,10)
        self.assertFalse(game.buy_item_from_npc(self.p,self.blade))
        self.assertEqual(self.p.ore_balance,10)

    def test_bulk_ammo_uses_full_price_and_cannot_buy_a_weapon_stack(self):
        ammo=ItemBluePrint.objects.create(name='Strzały',kind='ammo',stackable=True,base_value=1,original_stats={'ammo_type':'arrow'})
        self.assertTrue(game.buy_item_from_npc(self.p,ammo,20))
        self.assertEqual(self.p.ore_balance,30)
        self.assertEqual(self.p.inventory.get(blueprint=ammo).quantity,20)
        self.assertFalse(game.buy_item_from_npc(self.p,ammo,31))
        self.assertFalse(game.buy_item_from_npc(self.p,self.blade,2))
        for quantity in [0,-1,101,True]:self.assertFalse(game.buy_item_from_npc(self.p,ammo,quantity))
        self.assertEqual(self.p.ore_balance,30)
        self.client.post('/sklep/',{'action':'buy','buy_item_id':ammo.pk,'quantity':10,'price':0})
        self.p.refresh_from_db();self.assertEqual(self.p.ore_balance,20)
        self.assertEqual(self.p.inventory.get(blueprint=ammo).quantity,30)


class JourneyTests(TestCase):
    def setUp(self):self.p=User.objects.create_user('traveler').playerprofile
    def test_fresh_steps_point_at_a_real_available_quest_and_affordable_weapon(self):
        call_command('seed_story',stdout=StringIO())
        context=journey(self.p)
        self.assertEqual(context['chapter'],1)
        self.assertEqual(context['xp_remaining'],500)
        self.assertTrue(any('Dostępny przydział' in s['title'] for s in context['steps']))
        self.assertTrue(any('kind=weapon' in s['url'] for s in context['steps']))
    def test_ready_mining_has_priority_and_read_does_not_claim(self):
        self.p.action_end_time=timezone.now()-timedelta(seconds=1);self.p.save()
        before=type(self.p).objects.values().get(pk=self.p.pk)
        with CaptureQueriesContext(connection) as queries:context=journey(self.p)
        self.assertEqual(context['steps'][0]['title'],'Odbierz urobek')
        self.assertEqual(type(self.p).objects.values().get(pk=self.p.pk),before)
        self.assertLessEqual(len(queries),10)
    def test_completed_history_does_not_revert_header_to_chapter_one(self):
        quest=StoryQuest.objects.create(key='chapter-five',title='Raport',chapter=5,objectives=[],rewards={})
        StoryRun.objects.create(profile=self.p,quest=quest,status='claimed',snapshot={'key':quest.key,'chapter':5,'title':quest.title,'objectives':[]})
        other=StoryQuest.objects.create(key='side',title='Przysługa',chapter=1,objectives=[],rewards={})
        StoryRun.objects.create(profile=self.p,quest=other,snapshot={'key':other.key,'chapter':1,'title':other.title,'objectives':[]})
        self.assertEqual(journey(self.p)['chapter'],5)
        self.client.force_login(self.p.user)
        self.assertContains(self.client.get('/'),'Rozdział 5')
    def test_many_quests_do_not_issue_one_query_per_prerequisite(self):
        for i in range(35):StoryQuest.objects.create(key=f'locked-{i}',title='Zamknięty przydział',prerequisites=['missing'],objectives=[],rewards={})
        with CaptureQueriesContext(connection) as queries:journey(self.p)
        self.assertLessEqual(len(queries),10)


class HuntPreparationTests(TestCase):
    def setUp(self):self.p=User.objects.create_user('prepared').playerprofile
    def weapon(self,**kwargs):
        bp=ItemBluePrint.objects.create(name='Oręż',**kwargs);item=add_item(self.p,bp);game.equip_item(self.p,item);return item
    def test_ranged_missing_ammo_has_actionable_reason_and_no_consumption(self):
        self.weapon(damage=20,weapon_type='bow',damage_type='arrow')
        target={'life':40,'strength':8,'weapon_prot':2}
        before=type(self.p).objects.values().get(pk=self.p.pk)
        context=hunt_preparation(self.p,{'enemy':target})
        self.assertIn('amunicji',context['blocks'][0]['text'])
        self.assertEqual(type(self.p).objects.values().get(pk=self.p.pk),before)
        ammo=ItemBluePrint.objects.create(name='Strzała',kind='ammo',stackable=True,original_stats={'ammo_type':'arrow'})
        stack=add_item(self.p,ammo,3)
        self.assertFalse(hunt_preparation(self.p,{'enemy':target})['blocks'])
        stack.refresh_from_db();self.assertEqual(stack.quantity,3)
    def test_full_mastery_and_elemental_weapon_forecast_match_combat(self):
        self.weapon(damage=20,damage_type='fire')
        self.p.onehand_skill=100;self.p.save()
        target={'nazwa':'Przeciwnik','life':55,'strength':8,'weapon_prot':100,'fire_prot':0}
        context=hunt_preparation(self.p,{'enemy':target})
        self.assertEqual(context['forecasts']['enemy']['loss'],0)
        with patch('characters.game_logic.random.randint',side_effect=RuntimeError('must not roll')):
            self.assertEqual(hunt_preparation(self.p,{'enemy':target})['forecasts']['enemy']['loss'],0)
        result=game.simulate_combat(self.p,'unused',monster=target)
        self.assertEqual(result.remaining_health,self.p.current_health)
    def test_mana_and_busy_reason_replace_misleading_energy_error(self):
        bp=ItemBluePrint.objects.create(name='Zwój',kind='scroll',catalog_key='g1-itarscrollfirebolt')
        item=add_item(self.p,bp);self.p.prepared_magic=item;self.p.current_mana=0;self.p.save()
        context=hunt_preparation(self.p,{'enemy':{'life':12,'strength':3,'weapon_prot':0}})
        self.assertTrue(any('many' in b['text'] for b in context['blocks']))
        self.client.force_login(self.p.user)
        self.client.post('/polowanie/?location=exchange',{'monster_key':'young_scavenger','request_key':uuid4()})
        response=self.client.get('/polowanie/?location=exchange')
        self.assertContains(response,'Brakuje many')
    def test_risk_does_not_become_a_new_gameplay_gate(self):
        context=hunt_preparation(self.p,{'enemy':{'life':500,'strength':100,'weapon_prot':20}})
        self.assertEqual(context['forecasts']['enemy']['state'],'danger')
        self.assertFalse(context['blocks'])


class PublicIdentityTests(TestCase):
    def test_legacy_bot_topic_and_author_use_public_name_without_editing_history(self):
        bot=User.objects.create_user('colony-bot-500').playerprofile;bot.is_bot=True;bot.save()
        human=User.objects.create_user('visitor').playerprofile
        topic=TavernTopic.objects.create(author=bot,title='Wieści ze szlaku: colony-bot-500')
        from .models import TavernMessage
        TavernMessage.objects.create(topic=topic,author=bot,body='Prawdziwy zapis')
        self.client.force_login(human.user)
        response=self.client.get('/karczma/',{'topic':topic.pk})
        self.assertContains(response,bot.display_name)
        self.assertNotContains(response,'colony-bot-500')
        topic.refresh_from_db();self.assertEqual(topic.title,'Wieści ze szlaku: colony-bot-500')
    def test_life_page_uses_equipment_maximum_health(self):
        bot=User.objects.create_user('bot-health').playerprofile;bot.is_bot=True;bot.save()
        bp=ItemBluePrint.objects.create(name='Amulet',kind='amulet',life_bonus=30)
        game.equip_item(bot,add_item(bot,bp));bot.current_health=80;bot.save()
        self.client.force_login(User.objects.create_user('observer'))
        self.assertContains(self.client.get('/zycie-kolonii/'),'Zdrowie 80/80')
