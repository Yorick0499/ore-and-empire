from io import StringIO
from uuid import uuid4
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from .models import ItemBluePrint, OwnedItem, LootTable, BattleRecord
from . import game_logic as game
from .equipment import combat_values
from .bots import tick_bot


class EquipmentTests(TestCase):
    def setUp(self):
        self.hero = User.objects.create_user('geared').playerprofile
        self.weapon = ItemBluePrint.objects.create(name='Sword', damage=20, base_value=80)
        self.sword = OwnedItem.objects.create(owner=self.hero, blueprint=self.weapon)

    def item(self, kind, **kwargs):
        bp = ItemBluePrint.objects.create(name=kind, kind=kind, **kwargs)
        return OwnedItem.objects.create(owner=self.hero, blueprint=bp)

    def test_slots_stack_bonuses_without_replacing_weapon_and_remove_cleanly(self):
        armor = self.item('armor', weapon_prot=15)
        ring1 = self.item('ring', strength_bonus=5)
        ring2 = self.item('ring', weapon_prot=3)
        amulet = self.item('amulet', life_bonus=30)
        for item in (self.sword, armor, ring1, ring2, amulet): self.assertTrue(game.equip_item(self.hero,item))
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.inventory.filter(is_equipped=True).count(),5)
        self.assertEqual(combat_values(self.hero)[0],35)
        self.assertEqual(self.hero.effective_protection(),18)
        self.assertEqual((self.hero.life,self.hero.max_health,self.hero.current_health),(50,80,50))
        self.hero.current_health=75
        self.hero.save()
        self.assertTrue(game.unequip_item(self.hero,amulet))
        self.hero.refresh_from_db()
        self.assertEqual((self.hero.max_health,self.hero.current_health),(50,50))
        self.assertTrue(game.equip_item(self.hero,amulet))
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.current_health,50)  # No heal by swapping gear.
        self.assertTrue(game.unequip_item(self.hero,ring1))
        self.assertEqual(combat_values(self.hero)[0],30)
        self.assertEqual(self.hero.strength,10)

    def test_requirements_and_non_equippable_items_are_enforced(self):
        locked = self.item('armor', min_level=2, required_camp='OLD_CAMP')
        self.assertFalse(game.equip_item(self.hero,locked))
        self.assertFalse(game.equip_item(self.hero,self.item('material')))
        self.assertFalse(game.equip_item(self.hero,self.item('weapon',required_dexterity=20,weapon_type='bow')))
        self.hero.camp='OLD_CAMP'; self.hero.level=2; self.hero.save()
        self.assertTrue(game.equip_item(self.hero,locked))

    def test_ranged_uses_dexterity_skill_arrow_protection_and_one_ammo_per_battle(self):
        bow = self.item('weapon', weapon_type='bow', damage=20, damage_type='arrow')
        self.hero.dexterity=30; self.hero.bow_skill=100; self.hero.save()
        game.equip_item(self.hero,bow)
        self.assertEqual(combat_values(self.hero),(50,100,'arrow'))
        self.assertFalse(game.execute_hunt(self.hero,'young_scavenger','exchange'))
        ammo_bp=ItemBluePrint.objects.create(name='Arrow',kind='ammo',stackable=True,original_stats={'ammo_type':'arrow'})
        ammo=OwnedItem.objects.create(owner=self.hero,blueprint=ammo_bp,quantity=2)
        key=uuid4()
        self.assertTrue(game.execute_hunt(self.hero,'young_scavenger','exchange',key))
        self.assertTrue(game.execute_hunt(self.hero,'young_scavenger','exchange',key))
        ammo.refresh_from_db()
        self.assertEqual(ammo.quantity,1)
        self.assertEqual(BattleRecord.objects.count(),1)

    def test_loot_snapshot_replay_and_failure_rollback(self):
        game.equip_item(self.hero,self.sword)
        skin=ItemBluePrint.objects.create(name='Skin',kind='material',stackable=True)
        table=LootTable.objects.create(key='young_scavenger',version=7,entries=[{'blueprint':skin.pk,'weight':10000,'min':2,'max':2}])
        key=uuid4()
        first=game.execute_hunt(self.hero,'young_scavenger','exchange',key)
        self.hero.refresh_from_db(); before=(self.hero.experience,self.hero.current_energy)
        table.version=8; table.entries=[]; table.save()
        self.assertEqual(game.execute_hunt(self.hero,'young_scavenger','exchange',key),first)
        self.hero.refresh_from_db()
        self.assertEqual((self.hero.experience,self.hero.current_energy),before)
        self.assertEqual(self.hero.inventory.get(blueprint=skin).quantity,2)
        self.assertEqual(BattleRecord.objects.get().loot_version,7)
        table.entries=[{'blueprint':999999,'weight':10000}];table.save()
        with self.assertRaises(ItemBluePrint.DoesNotExist):
            game.execute_hunt(self.hero,'young_scavenger','exchange',uuid4())
        self.hero.refresh_from_db()
        self.assertEqual((self.hero.experience,self.hero.current_energy),before)
        self.assertEqual(BattleRecord.objects.count(),1)

    def test_defeat_no_loot_and_request_cannot_switch_target(self):
        skin=ItemBluePrint.objects.create(name='Skin',kind='material')
        LootTable.objects.create(key='young_scavenger',entries=[{'blueprint':skin.pk,'weight':10000}])
        key=uuid4()
        with patch('characters.game_logic.simulate_combat',return_value=game.CombatResult(False,['Defeat'],1)):
            game.execute_hunt(self.hero,'young_scavenger','exchange',key)
        self.assertFalse(self.hero.inventory.filter(blueprint=skin).exists())
        self.assertFalse(game.execute_hunt(self.hero,'meatbug','exchange',key))
        self.assertFalse(BattleRecord.objects.get().won)

    def test_consumable_stack_and_sale_are_real_resource_changes(self):
        potion=self.item('consumable',heal_amount=20,stackable=True,base_value=20)
        potion.quantity=3;potion.save()
        self.hero.current_health=10;self.hero.save()
        self.assertTrue(game.use_item(self.hero,potion))
        potion.refresh_from_db();self.hero.refresh_from_db()
        self.assertEqual((potion.quantity,self.hero.current_health),(2,30))
        self.assertTrue(game.sell_item_from_npc(self.hero,potion))
        self.hero.refresh_from_db();self.assertEqual(self.hero.ore_balance,70)
        self.assertFalse(game.use_item(self.hero,potion))

    def test_bot_equips_armor_and_does_not_sell_it_as_an_obsolete_weapon(self):
        self.hero.is_bot=True;self.hero.save()
        game.equip_item(self.hero,self.sword)
        armor=self.item('armor',weapon_prot=10)
        self.assertEqual(tick_bot(self.hero),('equip',True))
        armor.refresh_from_db()
        self.assertTrue(armor.is_equipped)
        self.assertEqual(armor.equipped_slot,'armor')

    def test_seed_is_idempotent_and_preserves_loot_edits(self):
        call_command('seed_equipment',stdout=StringIO())
        table=LootTable.objects.first();table.version=9;table.entries=[];table.save()
        total=ItemBluePrint.objects.count()
        call_command('seed_equipment',stdout=StringIO())
        table.refresh_from_db()
        self.assertEqual(ItemBluePrint.objects.count(),total)
        self.assertEqual(table.version,9)

    def test_boss_retry_returns_original_attempt_without_second_cost_or_drop(self):
        self.hero.level=6;self.hero.life=122;self.hero.current_health=122;self.hero.strength=100;self.hero.save()
        game.equip_item(self.hero,self.sword)
        key=uuid4()
        first=game.execute_boss(self.hero,'crawler_nest',key)
        self.hero.refresh_from_db(); before=(self.hero.experience,self.hero.ore_balance,self.hero.current_energy)
        second=game.execute_boss(self.hero,'crawler_nest',key)
        self.hero.refresh_from_db()
        self.assertEqual(first.pk,second.pk)
        self.assertEqual((self.hero.experience,self.hero.ore_balance,self.hero.current_energy),before)
        self.assertEqual(BattleRecord.objects.count(),1)

    def test_admin_item_removal_clears_cached_health_bonus(self):
        amulet=self.item('amulet',life_bonus=30)
        self.assertTrue(game.equip_item(self.hero,amulet))
        self.hero.current_health=75;self.hero.save()
        amulet.delete()
        self.hero.refresh_from_db()
        self.assertEqual((self.hero.equipment_health,self.hero.current_health),(0,50))

    def test_admin_blueprint_edit_and_owner_transfer_recompute_health(self):
        amulet=self.item('amulet',life_bonus=30)
        game.equip_item(self.hero,amulet)
        amulet.blueprint.life_bonus=40;amulet.blueprint.save()
        self.hero.refresh_from_db();self.assertEqual(self.hero.max_health,90)
        other=User.objects.create_user('receiver').playerprofile
        amulet.owner=other;amulet.save()
        self.hero.refresh_from_db();other.refresh_from_db()
        self.assertEqual((self.hero.max_health,other.max_health),(50,90))
