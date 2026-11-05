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

class BossBuildMatrixTests(TestCase):
    def test_controlled_melee_ranged_and_mage_builds_have_bounded_results(self):
        from .models import ItemBluePrint
        from .magic import BY_KEY,MagicPlan
        records=[]
        for build in ('warrior','archer','mage'):
            p=User.objects.create_user(build).playerprofile
            p.level=30;p.life=500;p.current_health=500;p.strength=250 if build=='warrior' else 10
            p.dexterity=250 if build=='archer' else 10;p.mana=300;p.current_mana=300
            p.weapon_prot=35;p.magic_prot=35;p.save()
            plan=None
            if build=='mage':plan=MagicPlan(BY_KEY['icewave'],0,False,1)
            else:
                bp=ItemBluePrint.objects.create(name=build,damage=75,weapon_type='bow' if build=='archer' else 'onehand',damage_type='arrow' if build=='archer' else 'weapon')
                OwnedItem.objects.create(owner=p,blueprint=bp,is_equipped=True,equipped_slot='weapon')
            for key,boss in BOSSES.items():
                result=game.simulate_combat(p,key,monster=boss.monster,magic_plan=plan)
                self.assertTrue(result.won,(build,key,result.log[-4:]))
                self.assertTrue(1<=result.remaining_health<=500)
                self.assertTrue(0<=result.remaining_mana<=300)
                records.append({'build':build,'boss':key,'won':result.won,'health_left':result.remaining_health,'mana_spent':300-result.remaining_mana})
        from .release_probe import record_scenario
        record_scenario('kontrolowana-macierz-buildow',{'synthetic_fixture':True,'encounters':records})


class SharedColonySessionTests(TestCase):
    def test_regular_player_levels_and_trades_while_bots_play_same_world(self):
        from .models import PlayerProfile,MarketTrade,BotDecision
        from .bots import tick_bot
        for command in ('seed_world','seed_equipment','seed_catalog','seed_adventures'):
            call_command(command,stdout=StringIO())
        call_command('run_bots',create=3,create_only=True,stdout=StringIO())
        response=self.client.post('/konto/rejestracja/',{'username':'MieszkaniecSesji','password1':'Droga-Przez-Kolonie-2026','password2':'Droga-Przez-Kolonie-2026'})
        self.assertEqual(response.status_code,302)
        player=User.objects.get(username='MieszkaniecSesji').playerprofile
        self.assertFalse(player.user.is_staff)
        bots=list(PlayerProfile.objects.filter(is_bot=True))
        now=timezone.now();actions=[]
        for step in range(40):
            with patch('django.utils.timezone.now',return_value=now+timedelta(minutes=10*step)):
                for bot in bots:
                    action,success=tick_bot(bot);self.assertTrue(success,(step,action));actions.append(action)
                player.refresh_from_db();game.refresh_player(player)
                offer=OwnedItem.objects.filter(is_market_listed=True,owner__is_bot=True,market_price__lte=player.ore_balance).first()
                if offer and not MarketTrade.objects.filter(buyer=player).exists():
                    self.assertEqual(self.client.post('/plac_targowy/',{'action':'buy','buy_item_id':offer.pk}).status_code,302)
                player.refresh_from_db()
                if player.action_end_time:
                    self.client.post('/kopalnia/',{'action':'claim'})
                elif step%4==0:
                    self.client.post('/kopalnia/',{'action':'mine'})
                elif player.skill_points>=1 and player.ore_balance>=10 and player.strength<20:
                    self.client.post('/trening/',{'attribute':'strength','count':1})
                else:
                    self.client.post('/polowanie/?location=exchange',{'monster_key':'young_scavenger','request_key':uuid4()})
        player.refresh_from_db()
        self.assertGreaterEqual(player.level,1)
        self.assertGreater(player.experience,0)
        self.assertTrue(MarketTrade.objects.filter(buyer=player,seller__is_bot=True).exists())
        self.assertFalse(BotDecision.objects.filter(success=False).exists())
        self.assertGreater(len(set(actions)),5)
        for bot in bots:
            bot.refresh_from_db();self.assertGreater(bot.experience,0)
        from .release_probe import record_scenario
        record_scenario('wspolna-sesja-gracza-i-botow',{'ticks':40,'bots':3,'level':player.level,'experience':player.experience,'real_bot_sales_to_player':MarketTrade.objects.filter(buyer=player,seller__is_bot=True).count(),'distinct_bot_actions':len(set(actions))})
