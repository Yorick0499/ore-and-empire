from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from uuid import uuid4
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase, Client
from django.utils import timezone
from . import game_logic as game
from .bosses import BOSSES, encounter_round
from .models import CampaignCompletion,EditionConclusion,BossAttempt,BattleRecord,StoryQuest,StoryRun,OwnedItem,LootTable
from .finale import conclude_edition

class FinaleTests(TestCase):
    def setUp(self):
        call_command('seed_equipment',stdout=StringIO())
        call_command('seed_story',stdout=StringIO())
        self.user=User.objects.create_user('warta');self.p=self.user.playerprofile
        self.client.force_login(self.user)
    def ready(self):
        self.p.level=30;self.p.strength=350;self.p.life=500;self.p.current_health=500;self.p.camp='OLD_CAMP';self.p.save()
        q=StoryQuest.objects.get(key='ritual-ready')
        StoryRun.objects.create(profile=self.p,quest=q,status='claimed',claimed_at=timezone.now(),snapshot={'key':q.key})
    def test_no_skipping_finale_retry_and_persistent_hall(self):
        self.p.level=30;self.p.save()
        self.assertFalse(game.execute_boss(self.p,'sleeper_sanctum'))
        self.assertFalse(CampaignCompletion.objects.exists())
        self.ready(); key=uuid4();attempt=game.execute_boss(self.p,'sleeper_sanctum',key)
        self.assertTrue(attempt.won)
        self.p.refresh_from_db();before=(self.p.experience,self.p.ore_balance,self.p.current_energy,self.p.inventory.count())
        self.assertEqual(game.execute_boss(self.p,'sleeper_sanctum',key).pk,attempt.pk)
        self.p.refresh_from_db();self.assertEqual(before,(self.p.experience,self.p.ore_balance,self.p.current_energy,self.p.inventory.count()))
        self.assertEqual(CampaignCompletion.objects.count(),1)
        self.assertContains(self.client.get('/sala-chwaly/'),'warta')
        self.assertTrue(self.p.world.is_current)
        self.assertTrue(self.p.inventory.filter(blueprint__catalog_key='seal-trophy').exists())
        self.assertContains(self.client.get('/ekwipunek/'),'Znak warty pieczęci')
    def test_seal_requires_operator_and_human_then_freezes_rankings_once(self):
        admin=User.objects.create_superuser('operator',password='Test-pass-2026')
        with self.assertRaises(PermissionDenied):conclude_edition(self.user,self.p.world_id,self.p.world.name)
        with self.assertRaises(ValidationError):conclude_edition(admin,self.p.world_id,self.p.world.name)
        self.ready();self.p.is_bot=True;self.p.save();game.execute_boss(self.p,'sleeper_sanctum')
        with self.assertRaises(ValidationError):conclude_edition(admin,self.p.world_id,self.p.world.name)
        self.p.is_bot=False;self.p.save()
        sealed=conclude_edition(admin,self.p.world_id,self.p.world.name);snapshot=sealed.snapshot
        self.p.experience+=100;self.p.save()
        self.assertEqual(conclude_edition(admin,self.p.world_id,self.p.world.name).snapshot,snapshot)
        self.assertEqual(EditionConclusion.objects.count(),1)
        self.assertTrue(game.start_mining(self.p,15))
    def test_boss_phases_telegraphs_defeat_and_atomic_loot_failure(self):
        m=BOSSES['swamp_den'].monster
        self.assertGreater(encounter_round(m,100,3)[1],encounter_round(m,100,4)[1])
        self.assertIn('następną',encounter_round(m,100,2)[4][0])
        self.assertEqual(encounter_round(BOSSES['sleeper_sanctum'].monster,300,3)[3],'magic')
        self.p.level=8;self.p.save()
        attempt=game.execute_boss(self.p,'swamp_den');self.assertFalse(attempt.won)
        self.assertFalse(self.p.inventory.exists())
        self.p.current_health=50;self.p.current_energy=100;self.p.save()
        with patch('django.utils.timezone.now',return_value=timezone.now()+timedelta(hours=1)):
            self.p.strength=500;self.p.save();before=(self.p.experience,self.p.ore_balance,self.p.current_energy)
            with patch('characters.loot.add_item',side_effect=RuntimeError('interrupted')):
                with self.assertRaises(RuntimeError):game.execute_boss(self.p,'swamp_den',uuid4())
        self.p.refresh_from_db();self.assertEqual(before,(self.p.experience,self.p.ore_balance,self.p.current_energy))
        self.assertEqual(BossAttempt.objects.count(),1)
    def test_all_bosses_have_distinct_loot_and_actual_phase_reports(self):
        tables=[LootTable.objects.get(key=k).entries for k in BOSSES]
        self.assertEqual(len({str(t) for t in tables}),3)
        self.p.life=500;self.p.current_health=500;self.p.strength=20;self.p.save()
        result=game.simulate_combat(self.p,'crawler_nest',monster=BOSSES['crawler_nest'].monster)
        self.assertTrue(result.won)
        self.assertTrue(any('Faza 2' in line for line in result.log))
        self.assertTrue(any('Faza 3' in line for line in result.log))
        self.assertTrue(any('Zapowiedziany' in line for line in result.log))
