"""Regressions found during the fresh-account and two-realm playtest."""
from uuid import uuid4
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from .models import World,ItemBluePrint,StoreProduct,StorePurchase
from .itemshop_rules import unavailable_reason,helpful,LIMITS
from .economy import purchase_product


class ShopExplanationTests(TestCase):
    def setUp(self):
        self.p=User.objects.create_user('shop-audit').playerprofile
        self.product=StoreProduct.objects.create(key='audit-energy',name='Napój próby',kind='energy',price=3,effect=25)

    def test_full_resource_explanation_and_no_charge(self):
        self.p.premium_balance=5;self.p.save()
        self.assertEqual(unavailable_reason(self.p,self.product,5),'Masz pełną energię.')
        self.assertFalse(purchase_product(self.p,self.product.pk,uuid4()))
        self.p.refresh_from_db();self.assertEqual(self.p.premium_balance,5)
        self.assertFalse(StorePurchase.objects.filter(profile=self.p).exists())

    def test_balance_and_shared_refill_limit_are_explained(self):
        self.p.current_energy=20;self.p.save()
        self.assertIn('Brakuje 3 odłamków',unavailable_reason(self.p,self.product,5))
        self.assertIn('limit odnowień energii',unavailable_reason(self.p,self.product,0))
        self.p.premium_balance=3;self.p.save()
        self.assertTrue(helpful(self.p,self.product,5))
        key=uuid4();first=purchase_product(self.p,self.product.pk,key)
        self.assertTrue(first);self.assertEqual(purchase_product(self.p,self.product.pk,key).pk,first.pk)
        self.p.refresh_from_db();self.assertEqual(self.p.premium_balance,0)
        self.assertEqual(StorePurchase.objects.filter(profile=self.p).count(),1)

    def test_daily_kind_caps_and_level_explanations(self):
        self.product.kind='xp';self.product.effect=150;self.product.level=3
        self.assertEqual(unavailable_reason(self.p,self.product,5),'Wymagany poziom: 3.')
        self.p.level=3;limits={kind:0 for kind in LIMITS}
        self.assertIn('limit zakupów',unavailable_reason(self.p,self.product,5,limits))

    def test_island_shop_hides_colony_items_and_rejects_crafted_post(self):
        island=World.objects.create(name='Wyspa próby',universe='GOTHIC_II',is_open=True,configured=True)
        self.p.world=island;self.p.premium_balance=100;self.p.save()
        bp=ItemBluePrint.objects.create(name='Oręż tylko Kolonii',source_game='GOTHIC_I',kind='weapon',damage=10)
        product=StoreProduct.objects.create(key='audit-colony',name=bp.name,kind='weapon',price=1,blueprint=bp)
        self.client.force_login(self.p.user)
        page=self.client.get('/sklep-odlamkow/')
        self.assertNotContains(page,bp.name);self.assertContains(page,'Masz pełną energię.')
        self.assertContains(page,'nie oznacza premium konta')
        self.assertFalse(purchase_product(self.p,product.pk,uuid4()))
        self.p.refresh_from_db();self.assertEqual(self.p.premium_balance,100)
        self.assertFalse(self.p.inventory.exists())

    def test_island_pages_identify_the_correct_world(self):
        from .world_management import seed_clean_world
        from django.core.management import call_command
        from io import StringIO
        seed_clean_world();world=self.p.world;world.configured=True;world.save()
        call_command('open_khorinis',bots=0,stdout=StringIO())
        self.p.world=World.objects.get(universe='GOTHIC_II',is_open=True);self.p.save()
        self.client.force_login(self.p.user)
        page=self.client.get('/')
        self.assertContains(page,'Gothic II: Noc Kruka')
        self.assertNotContains(page,'Warunki finału i sala chwały')
        shop=self.client.get('/sklep-odlamkow/')
        self.assertContains(shop,'Wróć do Khorinis');self.assertNotContains(shop,'Wróć do Górniczej Doliny')

    def test_completed_island_story_has_honest_next_steps(self):
        from .player_journey import journey
        from .test_new_progression import claim
        from .models import StoryQuest
        self.p.world.universe='GOTHIC_II';self.p.world.save()
        StoryQuest.objects.create(key='k2-supply-8',title='Warta',universe='GOTHIC_II')
        claim(self.p,'k2-supply-8')
        result=journey(self.p)
        self.assertTrue(result['island_complete']);self.assertFalse(result['finished'])
        self.assertTrue(any('Warta Khorinis ukończona' in step['title'] for step in result['steps']))
        self.assertFalse(any(step['url']=='/warty/' for step in result['steps']))


class IslandContentValidationTests(TestCase):
    def test_missing_art_and_foreign_hunt_are_detected(self):
        import json
        from .gothic_assets import MANIFEST_PATH
        from .khorinis import campaign
        from .management.commands.validate_content import validate_khorinis
        assets=json.loads(MANIFEST_PATH.read_text())
        self.assertEqual(validate_khorinis(assets),(29,16,8))
        del assets['k2_wolf']
        with self.assertRaisesRegex(ValueError,'artwork'):validate_khorinis(assets)
        assets=json.loads(MANIFEST_PATH.read_text());quests=campaign()
        quests[0]['objectives']=[{'kind':'hunt','target':'young_scavenger'}]
        with patch('characters.khorinis.campaign',return_value=quests):
            with self.assertRaisesRegex(ValueError,'Cross-world'):validate_khorinis(assets)
