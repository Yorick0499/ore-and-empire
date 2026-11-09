from datetime import timedelta
from io import StringIO
from uuid import uuid4
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase,Client
from django.utils import timezone
from .models import OwnedItem,ItemBluePrint,StoryQuest,StoryRun,MarketTrade,World,PlayerProfile
from . import game_logic as game
from .story_quests import accept_story,activate_story,claim_story,progress_for

class HostilePlayerTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('adversary',password='probe-password')
        self.p=self.user.playerprofile
        self.other=User.objects.create_user('victim').playerprofile
        self.item=OwnedItem.objects.create(owner=self.other,blueprint=ItemBluePrint.objects.create(name='Miecz próby',damage=12,base_value=10))
        self.client.force_login(self.user)
    def test_tampered_ids_admin_routes_gets_and_csrf_do_not_change_balances(self):
        before=(self.p.ore_balance,self.other.ore_balance,self.item.owner_id)
        for url,data in [('/ekwipunek/',{'action':'equip','item_id':self.item.pk}),('/sklep/',{'action':'sell','sell_item_id':self.item.pk}),('/plac_targowy/',{'action':'list','sell_item_id':self.item.pk,'item_price':100})]:
            self.assertEqual(self.client.post(url,data).status_code,404)
        for url in ['/zarzadca/','/zarzadca/swiat/reset/','/admin/']:
            self.assertNotEqual(self.client.get(url).status_code,200)
        for bad in ['-1','0','x','1 OR 1=1','9'*200]:
            self.assertEqual(self.client.post('/ekwipunek/',{'action':'use','item_id':bad}).status_code,404)
        secure=Client(enforce_csrf_checks=True);secure.force_login(self.user)
        self.assertEqual(secure.post('/kopalnia/',{'action':'mine'}).status_code,403)
        self.assertEqual(self.client.get('/kopalnia/?action=mine').status_code,200)
        self.p.refresh_from_db();self.other.refresh_from_db();self.item.refresh_from_db()
        self.assertEqual(before,(self.p.ore_balance,self.other.ore_balance,self.item.owner_id));self.assertIsNone(self.p.action_end_time)
    def test_repeated_sale_stale_ownership_and_negative_price_do_not_mint_currency(self):
        self.assertFalse(game.list_item_on_market(self.other,self.item,-10))
        self.assertFalse(game.list_item_on_market(self.other,self.item,True))
        self.assertTrue(game.list_item_on_market(self.other,self.item,10))
        stale=OwnedItem.objects.get(pk=self.item.pk)
        self.assertTrue(game.buy_item_on_market(self.p,self.item))
        self.assertFalse(game.buy_item_on_market(self.other,stale))
        self.p.refresh_from_db();self.other.refresh_from_db();self.item.refresh_from_db()
        self.assertEqual(self.p.ore_balance+self.other.ore_balance,100)
        self.assertEqual(MarketTrade.objects.count(),1)
        self.assertFalse(game.sell_item_from_npc(self.other,stale))
    def test_stack_delivery_consumes_exact_quantity_and_retry_never_pays_twice(self):
        bp=ItemBluePrint.objects.create(name='Zioła próby',kind='material',stackable=True,base_value=2)
        stack=OwnedItem.objects.create(owner=self.p,blueprint=bp,quantity=5)
        quest=StoryQuest.objects.create(key='stack-probe',title='Dostawa',description='Przynieś trzy zioła',objectives=[{'id':'herbs','kind':'item','target':bp.pk,'count':3,'label':'Zioła'}],rewards={'ore':7},energy_cost=0)
        run=accept_story(self.p,quest.pk);self.assertTrue(activate_story(self.p,run.pk))
        run.refresh_from_db();self.assertEqual(progress_for(self.p,run,quest.objectives[0]),3)
        self.assertTrue(claim_story(self.p,run.pk));self.assertFalse(claim_story(self.p,run.pk))
        stack.refresh_from_db();self.p.refresh_from_db()
        self.assertEqual((stack.quantity,self.p.ore_balance),(2,57))
    def test_other_world_cannot_transfer_or_bypass_battle_gates(self):
        archived=World.objects.create(name='Archiwum',status='archived')
        old=PlayerProfile.objects.create(user=self.user,slot=2,world=archived)
        self.assertFalse(game.start_mining(old,15))
        self.assertFalse(game.execute_boss(self.p,'sleeper_sanctum'))
        self.assertFalse(game.execute_hunt(self.p,'demon_lord','exchange'))
        self.assertFalse(game.execute_hunt(self.p,'young_scavenger','exchange','bad-uuid'))
        self.p.refresh_from_db();self.assertEqual(self.p.current_energy,100)
    def test_posted_rewards_and_premium_amount_are_ignored(self):
        call_command('seed_adventures',stdout=StringIO())
        from .models import AdventureTemplate
        template=AdventureTemplate.objects.order_by('level').first()
        response=self.client.post('/zadania/',{'action':'start','template':template.pk,'ore_reward':999999,'premium_reward':999999,'ends_at':'2000-01-01'})
        self.assertEqual(response.status_code,302)
        run=self.p.adventures.get();self.assertGreater(run.ends_at,timezone.now())
        self.assertLess(run.ore_reward,999999)
        self.assertEqual(self.client.post('/zadania/',{'action':'claim','run':run.pk}).status_code,302)
        run.refresh_from_db();self.assertIsNone(run.claimed_at)
        self.p.refresh_from_db();self.assertEqual(self.p.premium_balance,0)
    def test_batch_training_rejects_invalid_counts_and_charges_each_point(self):
        self.p.skill_points=5;self.p.save()
        before=(self.p.strength,self.p.skill_points,self.p.ore_balance)
        for count in [-1,0,11,True,1.5]:self.assertFalse(game.train_attribute(self.p,'strength',count))
        self.p.refresh_from_db();self.assertEqual(before,(self.p.strength,self.p.skill_points,self.p.ore_balance))
        self.assertTrue(game.train_attribute(self.p,'strength',3))
        self.p.refresh_from_db();self.assertEqual((self.p.strength,self.p.skill_points,self.p.ore_balance),(before[0]+3,2,20))
        self.assertFalse(game.train_attribute(self.p,'strength',3))
