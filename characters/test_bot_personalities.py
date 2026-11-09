from collections import Counter
from datetime import datetime,timedelta,timezone as utc
from io import StringIO
from unittest.mock import patch
from uuid import uuid4
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from .bot_personalities import PERSONAS,assignment,in_session,cycle_state,simulate_purchase,purchase_roll
from .world_clock import POLISH_TIME
from .models import PremiumEntry,StoreProduct,StorePurchase,EconomicEntry,OwnedItem,ItemBluePrint,AdminAction
from .bots import tick_bot,Observation,BaselinePolicyV20
from .economy import purchase_product

class PersonalityTests(TestCase):
    def setUp(self):
        self.p=User.objects.create_user('osobowosc').playerprofile
        self.p.is_bot=True;self.p.bot_personality='casual';self.p.bot_session_shift=0;self.p.save()
        self.now=datetime(2026,11,10,0,15,tzinfo=POLISH_TIME)
    def test_all_personas_have_expected_windows_and_population_is_staggered(self):
        self.assertEqual(set(Counter(assignment(n,1)[0] for n in range(1,101))),set(PERSONAS))
        for key,definition in PERSONAS.items():
            self.p.bot_personality=key
            self.assertEqual(sum(in_session(self.p,self.now.replace(hour=0,minute=0)+timedelta(minutes=m)) for m in range(1440)),sum(d for _,d in definition.windows))
        for hour in range(24):
            active=0
            for n in range(1,101):
                self.p.bot_personality,self.p.bot_session_shift=assignment(n,1)
                active+=in_session(self.p,self.now.replace(hour=hour))
            self.assertTrue(0<active<100,(hour,active))
    def test_offline_and_cadence_do_not_create_fake_activity(self):
        with patch('django.utils.timezone.now',return_value=self.now.replace(hour=12)):
            self.assertEqual(tick_bot(self.p),('offline',True))
        self.assertFalse(self.p.botdecision_set.exists())
        self.p.bot_last_tick=self.now;self.p.save()
        with patch('django.utils.timezone.now',return_value=self.now+timedelta(seconds=20)):
            self.assertEqual(tick_bot(self.p),('idle',True))
        self.assertFalse(self.p.botdecision_set.exists())
    def test_dst_does_not_duplicate_purchase_reference_and_next_change_is_real(self):
        self.p.bot_personality='patron'
        first=datetime(2026,10,25,0,30,tzinfo=utc.utc)
        self.assertEqual(purchase_roll(self.p,first)[1],purchase_roll(self.p,first+timedelta(hours=1))[1])
        spring=datetime(2026,3,29,0,59,tzinfo=utc.utc)
        self.assertTrue(in_session(self.p,spring));self.assertFalse(in_session(self.p,spring+timedelta(minutes=1)))
        self.assertEqual(cycle_state(self.p,spring)['next'],datetime(2026,3,29,1,tzinfo=utc.utc))
    def test_simulated_purchase_is_capped_idempotent_and_audited(self):
        self.p.bot_personality='patron';self.p.save()
        with patch('django.utils.timezone.now',return_value=self.now):
            for slot in range(4):
                reference=f'bot-topup:1:{self.p.pk}:2026-11-10:{slot}'
                with patch('characters.bot_personalities.purchase_roll',return_value=(10,reference)):
                    simulate_purchase(self.p);simulate_purchase(self.p)
        self.p.refresh_from_db();self.assertEqual(self.p.premium_balance,24)
        self.assertEqual(PremiumEntry.objects.count(),3)
        self.assertEqual(sum(EconomicEntry.objects.filter(operation='simulated_purchase').values_list('amount',flat=True)),24)
    def test_humans_and_disabled_world_cannot_receive_simulated_purchases(self):
        with patch('django.utils.timezone.now',return_value=self.now),patch('characters.bot_personalities.purchase_roll',return_value=(10,'test-topup')):
            self.p.is_bot=False;self.p.save();self.assertEqual(simulate_purchase(self.p),0)
            self.p.is_bot=True;self.p.save();self.p.world.bot_simulated_purchases=False;self.p.world.save();self.assertEqual(simulate_purchase(self.p),0)
        self.assertFalse(PremiumEntry.objects.exists())
    def test_patron_spends_during_story_but_does_not_interrupt_rewards(self):
        o=Observation(energy=100,ore=100,busy=False,reward_ready=False,offer_id=None,inventory_id=None,blueprint_id=None,equip_id=None,armed=True,personality='patron',product_id=1,turn=4,story_action='story_talk',story_target=2,camp='OLD_CAMP')
        self.assertEqual(BaselinePolicyV20().choose(o),('shop',1))
        from dataclasses import replace
        self.assertEqual(BaselinePolicyV20().choose(replace(o,reward_ready=True)),('claim',None))

    def test_offline_rewards_and_regeneration_wait_for_the_next_session(self):
        from .models import AdventureTemplate,AdventureRun
        template=AdventureTemplate.objects.create(key='powrot',name='Powrót',duration_seconds=60)
        now=self.now.replace(hour=12)
        run=AdventureRun.objects.create(profile=self.p,template=template,ends_at=now-timedelta(minutes=1),ore_reward=10,experience_reward=80,premium_reward=0)
        self.p.current_energy=0;self.p.current_health=1;self.p.energy_updated_at=self.p.health_updated_at=now;self.p.save()
        with patch('django.utils.timezone.now',return_value=now):self.assertEqual(tick_bot(self.p),('offline',True))
        run.refresh_from_db();self.assertIsNone(run.claimed_at)
        with patch('django.utils.timezone.now',return_value=now+timedelta(hours=12)):
            self.assertEqual(tick_bot(self.p),('adventure_claim',True))
        self.p.refresh_from_db();self.assertEqual((self.p.current_energy,self.p.current_health),(100,50))
    def test_audit_failure_rolls_back_simulated_purchase(self):
        self.p.bot_personality='patron';self.p.save()
        with patch('django.utils.timezone.now',return_value=self.now),patch('characters.bot_personalities.purchase_roll',return_value=(10,'bot-topup:rollback')),patch('characters.economy.PremiumEntry.objects.create',side_effect=RuntimeError('audit')):
            with self.assertRaises(RuntimeError):simulate_purchase(self.p)
        self.p.refresh_from_db();self.assertEqual(self.p.premium_balance,0)
        self.assertFalse(PremiumEntry.objects.exists())

class ShopAndAdminTests(TestCase):
    def setUp(self):
        from .world_management import seed_clean_world
        seed_clean_world()
        self.p=User.objects.create_user('klient').playerprofile
        self.p.level=10;self.p.premium_balance=200;self.p.save()
    def test_seventeen_products_and_admin_edits_are_preserved(self):
        self.assertEqual(StoreProduct.objects.count(),17)
        q=StoreProduct.objects.get(key='diego-notes');q.price=9;q.save()
        call_command('seed_adventures',stdout=StringIO());q.refresh_from_db();self.assertEqual(q.price,9)
    def test_xp_shared_limit_retry_and_polish_midnight(self):
        q=StoreProduct.objects.get(key='diego-notes');before=self.p.experience
        now=datetime(2026,7,3,23,59,tzinfo=POLISH_TIME)
        with patch('django.utils.timezone.now',return_value=now):
            for _ in range(3):
                key=uuid4();first=purchase_product(self.p,q.pk,key);self.assertTrue(first)
                self.assertEqual(purchase_product(self.p,q.pk,key).pk,first.pk)
            self.assertFalse(purchase_product(self.p,q.pk,uuid4()))
        with patch('django.utils.timezone.now',return_value=now+timedelta(minutes=2)):
            self.assertTrue(purchase_product(self.p,q.pk,uuid4()))
        self.p.refresh_from_db();self.assertEqual(self.p.experience,before+600)
    def test_full_resource_and_mana_limit(self):
        q=StoreProduct.objects.get(key='mana-draught');self.p.mana=50;self.p.current_mana=50;self.p.save()
        self.assertFalse(purchase_product(self.p,q.pk,uuid4()))
        for _ in range(5):
            self.p.current_mana=0;self.p.save();self.assertTrue(purchase_product(self.p,q.pk,uuid4()))
        self.p.current_mana=0;self.p.save();self.assertFalse(purchase_product(self.p,q.pk,uuid4()))
    def test_dust_pack_costs_and_limit(self):
        q=StoreProduct.objects.get(key='small-rune-dust')
        for _ in range(2):self.assertTrue(purchase_product(self.p,q.pk,uuid4()))
        self.assertFalse(purchase_product(self.p,q.pk,uuid4()))
        self.p.refresh_from_db();self.assertEqual(self.p.premium_balance,188)
        self.assertEqual(self.p.inventory.get(blueprint=q.blueprint).quantity,10)
    def test_admin_grant_records_rarity_and_never_changes_existing_item(self):
        from .admin_tools import administer_player
        admin=User.objects.create_superuser('operator',password='Synthetic-Test-Only')
        bp=ItemBluePrint.objects.filter(kind='weapon').first()
        self.assertFalse(administer_player(self.p.user,self.p.pk,'item',{'blueprint':bp.pk,'rarity':4})[0])
        self.assertTrue(administer_player(admin,self.p.pk,'item',{'blueprint':bp.pk,'rarity':4,'quantity':2})[0])
        self.assertEqual(list(self.p.inventory.values_list('rarity','upgrade_level')),[(4,0),(4,0)])
        self.assertEqual(AdminAction.objects.get().details['rarity'],4)
        material=ItemBluePrint.objects.filter(kind='material').first()
        self.assertFalse(administer_player(admin,self.p.pk,'item',{'blueprint':material.pk,'rarity':3})[0])
