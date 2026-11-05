from pathlib import Path
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.core.exceptions import PermissionDenied,ValidationError
from django.db import IntegrityError,transaction
from .models import World,PlayerProfile,OwnedItem,ItemBluePrint,CampGuild
from .worlds import current_world
from .world_management import reset_world,initialize_world
from . import game_logic as game

class WorldManagementTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_superuser('zarzadca',password='Wlasne-Haslo-2026')
        self.user=User.objects.create_user('resident');self.world=current_world()
    def test_character_world_context_and_cross_world_actions_are_isolated(self):
        other=World.objects.create(name='Archiwum',status='archived')
        old=PlayerProfile.objects.create(user=self.user,world=other,ore_balance=900)
        self.assertFalse(game.start_mining(old,15))
        with self.assertRaises(IntegrityError),transaction.atomic():PlayerProfile.objects.create(user=self.user,world=self.world)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post('/postacie/',{'profile':old.pk}).status_code,404)
        p=User.objects.create_user('foreign').playerprofile;p.world=other;p.save()
        bp=ItemBluePrint.objects.create(name='Foreign sword',base_value=1)
        item=OwnedItem.objects.create(owner=p,blueprint=bp,is_market_listed=True,market_price=1)
        self.assertFalse(game.buy_item_on_market(self.user.playerprofile,item))
        self.assertNotContains(self.client.get('/plac_targowy/'),'Foreign sword')
    def test_reset_requires_admin_password_world_name_and_fresh_world_id(self):
        values=dict(name='Nowa Kolonia',bot_count=2,password='wrong',confirmation=self.world.name,expected_world=self.world.pk)
        with self.assertRaises(PermissionDenied):reset_world(self.admin,**values)
        values['password']='Wlasne-Haslo-2026';values['confirmation']='wrong'
        with self.assertRaises(ValidationError):reset_world(self.admin,**values)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
        self.client.force_login(self.user);self.assertEqual(self.client.get('/zarzadca/swiat/reset/').status_code,403)
    @patch('characters.backups.create_backup',return_value=Path('/private/test-backup'))
    def test_full_reset_preserves_admin_credentials_clears_progress_and_creates_requested_bots(self,backup):
        bp=ItemBluePrint.objects.create(name='Legacy item');OwnedItem.objects.create(owner=self.user.playerprofile,blueprint=bp)
        fresh,_=reset_world(self.admin,name='Nowa Kolonia',bot_count=2,password='Wlasne-Haslo-2026',confirmation=self.world.name,expected_world=self.world.pk)
        self.admin.refresh_from_db();self.assertTrue(self.admin.check_password('Wlasne-Haslo-2026'))
        self.assertFalse(User.objects.filter(username='resident').exists());self.assertFalse(ItemBluePrint.objects.filter(name='Legacy item').exists())
        self.assertEqual((fresh.name,fresh.bot_count,fresh.edition),('Nowa Kolonia',2,2))
        self.assertEqual(PlayerProfile.objects.filter(world=fresh,is_bot=True).count(),2)
        self.assertEqual(CampGuild.objects.filter(world=fresh).count(),3)
        self.assertEqual(self.admin.playerprofile.world_id,fresh.pk)
    @patch('characters.backups.create_backup',return_value=Path('/private/test-backup'))
    def test_reset_rolls_back_when_seeding_fails(self,backup):
        with patch('characters.world_management.seed_clean_world',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):reset_world(self.admin,name='Nowy',bot_count=0,password='Wlasne-Haslo-2026',confirmation=self.world.name,expected_world=self.world.pk)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists());self.assertEqual(current_world().pk,self.world.pk)
    def test_existing_admin_closes_bootstrap_and_configuration_does_not_reset(self):
        with self.assertRaises(PermissionDenied):initialize_world('Test',1,'new-admin','Bezpieczny-Test-2026')
        self.client.force_login(self.admin)
        self.client.post('/zarzadca/swiat/reset/',{'action':'configure','name':'Kolonia Testowa','bot_count':0})
        self.assertEqual(current_world().name,'Kolonia Testowa');self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

class WorldInitializationTests(TestCase):
    def test_first_setup_requires_chosen_valid_credentials_and_creates_requested_population(self):
        with self.assertRaises(ValidationError):initialize_world('Mój świat',1,'new-admin','123')
        admin=initialize_world('Mój świat',1,'new-admin','Wlasne-Silne-Haslo-2026')
        self.assertTrue(admin.check_password('Wlasne-Silne-Haslo-2026'))
        self.assertEqual((current_world().name,current_world().bot_count),('Mój świat',1))
        self.assertEqual(PlayerProfile.objects.filter(is_bot=True).count(),1)
        with self.assertRaises(PermissionDenied):initialize_world('Inny',0,'second','Wlasne-Silne-Haslo-2026')
