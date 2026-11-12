"""Do not retain ammunition for weapons a bot no longer uses."""
from django.test import TestCase
from django.contrib.auth.models import User
from .models import ItemBluePrint,OwnedItem
from .world_management import seed_clean_world
from .bots import tick_bot

class BotInventoryTests(TestCase):
    def setUp(self):
        seed_clean_world();self.p=User.objects.create_user('ammo-cleanup').playerprofile
        self.p.is_bot=True;self.p.camp='OLD_CAMP';self.p.guild='BARON';self.p.level=30;self.p.strength=150;self.p.ore_balance=1000;self.p.bot_turn=1;self.p.save()
        for kind,slot in [('weapon','weapon'),('armor','armor'),('amulet','amulet'),('ring','ring1'),('ring','ring2')]:
            bp=ItemBluePrint.objects.create(name='Fixture '+slot,kind=kind,weapon_type='onehand' if kind=='weapon' else '',damage=100 if kind=='weapon' else 0,source_game='adaptation')
            OwnedItem.objects.create(owner=self.p,blueprint=bp,is_equipped=True,equipped_slot=slot)
        self.bp=ItemBluePrint.objects.create(name='Spare arrows',kind='ammo',base_value=2,stackable=True,source_game='adaptation',original_stats={'ammo_type':'arrow'})
        self.arrows=OwnedItem.objects.create(owner=self.p,blueprint=self.bp,quantity=10)
    def test_melee_bot_sells_unused_ammunition_through_npc_service(self):
        class SellPolicy:
            def choose(self,o):return 'sell',o.disposal_id
        self.assertEqual(tick_bot(self.p,policy=SellPolicy(),force_active=True),('sell',True))
        self.assertFalse(OwnedItem.objects.filter(pk=self.arrows.pk).exists())
        self.p.refresh_from_db();self.assertEqual(self.p.ore_balance,1010)
    def test_current_bow_ammunition_is_reserved(self):
        weapon=self.p.inventory.get(equipped_slot='weapon').blueprint;weapon.weapon_type='bow';weapon.save()
        seen=[]
        class ObservePolicy:
            def choose(self,o):seen.append(o.disposal_id);return 'wait',None
        self.assertEqual(tick_bot(self.p,policy=ObservePolicy(),force_active=True),('wait',True))
        self.assertEqual(seen,[None]);self.arrows.refresh_from_db();self.assertEqual(self.arrows.quantity,10)
