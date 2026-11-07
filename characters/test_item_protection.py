from uuid import uuid4
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from . import game_logic as game
from .crafting import craft_item, recipe_cards
from .enhancements import improve_item, salvage_item
from .equipment import set_item_protection, add_item
from .models import CraftRecipe, EquipmentWork, ItemBluePrint, OwnedItem, StoryQuest
from .story_quests import accept_story, activate_story, claim_story, ready


class ItemProtectionTests(TestCase):
    def setUp(self):
        self.profile = User.objects.create_user('keeper').playerprofile
        self.other = User.objects.create_user('outsider').playerprofile
        self.blueprint = ItemBluePrint.objects.create(name='Miecz kopacza', kind='weapon', damage=15, base_value=100)
        self.item = OwnedItem.objects.create(owner=self.profile, blueprint=self.blueprint, origin='loot')
        self.dust = ItemBluePrint.objects.create(catalog_key='rune-dust', name='Pył', kind='material', stackable=True)

    def protect(self):
        self.assertTrue(set_item_protection(self.profile, self.item.pk, True))

    def test_stale_objects_cannot_sell_list_or_salvage_protected_item(self):
        self.protect()  # self.item intentionally still has the old False value.
        before = self.profile.ore_balance
        self.assertFalse(game.sell_item_from_npc(self.profile, self.item))
        self.assertFalse(game.list_item_on_market(self.profile, self.item, 100))
        self.assertFalse(salvage_item(self.profile, self.item.pk, uuid4()))
        self.item.refresh_from_db(); self.profile.refresh_from_db()
        self.assertTrue(self.item.is_protected)
        self.assertEqual(self.profile.ore_balance, before)
        self.assertFalse(EquipmentWork.objects.exists())

    def test_repeated_form_sets_state_and_unequip_upgrade_remain_possible(self):
        self.profile.ore_balance = 1000; self.profile.save()
        add_item(self.profile, self.dust, 10)
        self.protect(); self.protect()
        self.assertTrue(game.equip_item(self.profile, self.item))
        self.assertTrue(improve_item(self.profile, self.item.pk, 0, uuid4()))
        self.assertTrue(game.unequip_item(self.profile, self.item))
        self.item.refresh_from_db()
        self.assertEqual(self.item.upgrade_level, 1)
        self.assertTrue(self.item.is_protected)
        self.assertTrue(set_item_protection(self.profile, self.item.pk, False))
        self.assertTrue(set_item_protection(self.profile, self.item.pk, False))
        self.assertTrue(game.sell_item_from_npc(self.profile, self.item))

    def test_foreign_listed_non_equippable_and_invalid_states_are_rejected(self):
        self.assertFalse(set_item_protection(self.other, self.item.pk, True))
        self.assertFalse(set_item_protection(self.profile, self.item.pk, '1'))
        self.assertFalse(set_item_protection(self.profile, add_item(self.profile, self.dust).pk, True))
        self.assertTrue(game.list_item_on_market(self.profile, self.item, 100))
        self.assertFalse(set_item_protection(self.profile, self.item.pk, True))
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_protected)
        with self.assertRaises(IntegrityError), transaction.atomic():
            OwnedItem.objects.filter(pk=self.item.pk).update(is_protected=True)

    def test_protected_items_are_not_crafting_ingredients(self):
        self.profile.smithing_skill = 1; self.profile.save()
        recipe = CraftRecipe.objects.create(key='reuse', name='Przekucie', discipline='smithing', skill=1,
            output=self.blueprint, fee=0, ingredients=[{'blueprint':self.blueprint.pk, 'count':1}])
        self.protect()
        card = next(c for c in recipe_cards(self.profile) if c['recipe'].pk == recipe.pk)
        self.assertFalse(card['can_craft']); self.assertEqual(card['ingredients'][0]['have'], 0)
        self.assertFalse(craft_item(self.profile, recipe.pk, uuid4()))
        self.assertTrue(OwnedItem.objects.filter(pk=self.item.pk).exists())
        self.assertTrue(set_item_protection(self.profile, self.item.pk, False))
        self.assertTrue(craft_item(self.profile, recipe.pk, uuid4()))

    def test_protected_delivery_does_not_grant_story_rewards(self):
        quest = StoryQuest.objects.create(key='delivery-protection', title='Dostawa', description='Dostawa',
            objectives=[{'id':'item','kind':'item','target':self.blueprint.pk,'count':1,'label':'Miecz'}], rewards={'ore':30})
        run = accept_story(self.profile, quest.pk)
        self.assertTrue(activate_story(self.profile, run.pk))
        self.protect(); run.refresh_from_db()
        self.assertFalse(ready(self.profile, run))
        before = self.profile.ore_balance
        self.assertFalse(claim_story(self.profile, run.pk))
        self.profile.refresh_from_db(); self.assertEqual(self.profile.ore_balance, before)
        self.assertTrue(set_item_protection(self.profile, self.item.pk, False))
        self.assertTrue(claim_story(self.profile, run.pk))
        self.assertFalse(OwnedItem.objects.filter(pk=self.item.pk).exists())

    def test_ui_and_forged_post_apply_same_rules(self):
        self.client.force_login(self.profile.user)
        response = self.client.post('/ekwipunek/', {'action':'protect','item_id':self.item.pk,'protected':'1'}, follow=True)
        self.assertContains(response, 'Zabezpieczony przed utratą')
        self.assertNotContains(response, 'Rozbierz na pył (zużywa przedmiot)')
        self.client.post('/sklep/', {'action':'sell','sell_item_id':self.item.pk})
        self.client.post('/plac_targowy/', {'action':'list','sell_item_id':self.item.pk,'item_price':100})
        self.item.refresh_from_db(); self.assertFalse(self.item.is_market_listed)
        self.client.force_login(self.other.user)
        self.client.post('/ekwipunek/', {'action':'protect','item_id':self.item.pk,'protected':'0'})
        self.item.refresh_from_db(); self.assertTrue(self.item.is_protected)

    def test_new_loot_does_not_merge_into_a_protected_legacy_stack(self):
        self.blueprint.stackable = True; self.blueprint.save()
        self.protect()
        new = add_item(self.profile, self.blueprint, 2, origin='loot')
        self.assertNotEqual(new.pk, self.item.pk)
        self.item.refresh_from_db(); self.assertEqual(self.item.quantity, 1)
