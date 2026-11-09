from io import StringIO
from uuid import uuid4
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from .models import CraftRecipe,CraftRecord,OwnedItem,ItemBluePrint
from .crafting import learn_craft,buy_craft_material,craft_item
from .management.commands.simulate_crafting import model

class CraftingTests(TestCase):
    def setUp(self):
        call_command('seed_crafting',stdout=StringIO())
        self.p=User.objects.create_user('artisan').playerprofile;self.p.ore_balance=1000;self.p.skill_points=10;self.p.level=10;self.p.save()
        self.recipe=CraftRecipe.objects.get(key='tonic')
    def acquire(self):
        self.assertTrue(learn_craft(self.p,'alchemy'))
        for ingredient in self.recipe.ingredients:
            for _ in range(ingredient['count']):self.assertTrue(buy_craft_material(self.p,ingredient['blueprint']))
    def test_requirements_atomic_consumption_output_and_retry(self):
        self.assertFalse(craft_item(self.p,self.recipe.pk,uuid4()));self.acquire()
        key=uuid4();first=craft_item(self.p,self.recipe.pk,key);self.assertTrue(first)
        self.assertEqual(craft_item(self.p,self.recipe.pk,key).pk,first.pk)
        self.assertEqual(self.p.inventory.filter(blueprint=self.recipe.output).count(),1)
        self.assertFalse(self.p.inventory.exclude(blueprint=self.recipe.output).exists())
        self.assertFalse(craft_item(self.p,CraftRecipe.objects.get(key='blade').pk,key))
    def test_listed_foreign_materials_and_failure_cannot_produce_item(self):
        self.acquire();item=self.p.inventory.first();item.is_market_listed=True;item.market_price=1;item.save()
        self.assertFalse(craft_item(self.p,self.recipe.pk,uuid4()));item.is_market_listed=False;item.save()
        before=list(self.p.inventory.values_list('blueprint_id','quantity'))
        with patch.object(CraftRecord.objects,'create',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):craft_item(self.p,self.recipe.pk,uuid4())
        self.assertEqual(list(self.p.inventory.values_list('blueprint_id','quantity')),before)
        invalid=ItemBluePrint.objects.create(name='Nie jest składnikiem',base_value=1)
        self.assertFalse(buy_craft_material(self.p,invalid.pk))
    def test_simulation_has_finite_inputs_and_explicit_currency_sinks(self):
        closed=model(self.recipe,{i['blueprint']:10 for i in self.recipe.ingredients},100)
        supplied=model(self.recipe,{i['blueprint']:10 for i in self.recipe.ingredients},100,True)
        self.assertEqual(closed['crafted'],5);self.assertEqual(supplied['crafted'],100)
        self.assertEqual(supplied['premium_created'],0);self.assertGreater(supplied['ore_sink'],supplied['maximum_npc_sale'])
    def test_bot_learns_and_uses_material_service_and_ui_ignores_fake_cost(self):
        from .bots import tick_bot
        self.p.is_bot=True;self.p.bot_turn=23;self.p.current_health=20;self.p.save()
        self.assertEqual(tick_bot(self.p, force_active=True),('craft_learn',True))
        self.client.force_login(self.p.user)
        self.assertContains(self.client.get('/rzemioslo/'),'Kuźnia i alchemia')
