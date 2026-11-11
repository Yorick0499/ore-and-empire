from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from uuid import uuid4
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import IntegrityError,transaction
from django.test import TestCase,SimpleTestCase
from django.utils import timezone
from .models import ItemBluePrint,OwnedItem,EquipmentWork,CampaignCompletion,BossAttempt,FrontierProgress,FrontierRecord,PlayerProfile,World
from .equipment import add_item,combat_values
from .enhancements import improve_item,salvage_item
from .frontier import patrol,board,season_key
from . import game_logic as game


class EndgameTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_equipment',stdout=StringIO())
    def setUp(self):
        self.user=User.objects.create_user('wartownik');self.p=self.user.playerprofile
        self.p.ore_balance=10000;self.p.save()
        self.gear=add_item(self.p,ItemBluePrint.objects.get(catalog_key='colony-loot-0-onehand'))
        self.dust=add_item(self.p,ItemBluePrint.objects.get(catalog_key='rune-dust'),200)
        self.client.force_login(self.user)
    def finish(self):
        self.p.level=30;self.p.life=1000;self.p.current_health=1000;self.p.strength=300;self.p.camp='OLD_CAMP';self.p.save()
        battle=BossAttempt.objects.create(profile=self.p,boss_key='sleeper_sanctum',won=True)
        CampaignCompletion.objects.create(profile=self.p,battle=battle)
    def test_upgrade_replay_stale_request_stats_and_trade_preservation(self):
        game.equip_item(self.p,self.gear);key=uuid4();before=combat_values(self.p)[0]
        self.assertTrue(improve_item(self.p,self.gear.pk,0,key))
        self.assertEqual(improve_item(self.p,self.gear.pk,0,key).pk,EquipmentWork.objects.get().pk)
        self.assertFalse(improve_item(self.p,self.gear.pk,0,uuid4()))
        self.gear.refresh_from_db();self.p.refresh_from_db();self.dust.refresh_from_db()
        self.assertEqual((self.gear.upgrade_level,self.p.ore_balance,self.dust.quantity),(1,9940,197))
        self.assertEqual(combat_values(self.p)[0],before+1)
        self.assertEqual(self.gear.blueprint.damage,12)
        game.unequip_item(self.p,self.gear);game.list_item_on_market(self.p,self.gear,40)
        other=User.objects.create_user('kupujacy').playerprofile
        self.assertFalse(improve_item(other,self.gear.pk,1,uuid4()))
        self.assertFalse(improve_item(self.p,self.gear.pk,1,uuid4()))
        self.assertTrue(game.buy_item_on_market(other,self.gear))
        self.gear.refresh_from_db();self.assertEqual((self.gear.owner_id,self.gear.upgrade_level),(other.pk,1))
    def test_five_named_ranks_material_sink_and_cap(self):
        self.p.ore_balance=100000;self.p.save()
        for level in range(3):self.assertTrue(improve_item(self.p,self.gear.pk,level,uuid4()))
        self.assertFalse(improve_item(self.p,self.gear.pk,3,uuid4()))
        self.dust.refresh_from_db();self.assertEqual(self.dust.quantity,167)
        self.gear.refresh_from_db();self.assertEqual(self.gear.effective_stats['damage'],15)
    def test_upgrade_does_not_heal_and_rolls_back_all_costs(self):
        amulet=add_item(self.p,ItemBluePrint.objects.get(catalog_key='colony-loot-0-amulet'));game.equip_item(self.p,amulet)
        self.p.current_health=20;self.p.current_mana=3;self.p.save()
        self.assertTrue(improve_item(self.p,amulet.pk,0,uuid4()));self.p.refresh_from_db()
        self.assertEqual((self.p.current_health,self.p.current_mana),(20,3))
        with patch('characters.enhancements.EquipmentWork.objects.create',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):improve_item(self.p,self.gear.pk,0,uuid4())
        self.gear.refresh_from_db();self.dust.refresh_from_db();self.p.refresh_from_db()
        self.assertEqual((self.gear.upgrade_level,self.dust.quantity,self.p.ore_balance),(0,197,9940))
    def test_salvage_ownership_no_equipped_or_merchant_item_and_replay(self):
        key=uuid4();self.assertTrue(salvage_item(self.p,self.gear.pk,key));self.assertTrue(salvage_item(self.p,self.gear.pk,key))
        self.dust.refresh_from_db();self.assertEqual(self.dust.quantity,202)
        self.assertFalse(salvage_item(self.p,self.gear.pk,uuid4()))
        merchant=add_item(self.p,ItemBluePrint.objects.get(catalog_key='starter-leather'))
        self.assertFalse(salvage_item(self.p,merchant.pk,uuid4()))
    def test_patrol_gate_progress_replay_cooldown_and_no_client_rewards(self):
        self.assertFalse(patrol(self.p,1,uuid4()));self.finish()
        self.assertFalse(patrol(self.p,2,uuid4()));key=uuid4();row=patrol(self.p,1,key);self.assertTrue(row.won)
        self.assertEqual(len(row.snapshot['loot']),2)
        before=(self.p.experience,self.p.ore_balance,self.p.current_energy,self.p.inventory.count())
        self.assertEqual(patrol(self.p,1,key).pk,row.pk)
        self.assertFalse(patrol(self.p,2,key));self.assertFalse(patrol(self.p,2,uuid4()))
        self.p.refresh_from_db();self.assertEqual(before,(self.p.experience,self.p.ore_balance,self.p.current_energy,self.p.inventory.count()))
        FrontierProgress.objects.filter(profile=self.p).update(last_attempt_at=timezone.now()-timedelta(minutes=6))
        self.assertTrue(patrol(self.p,2,uuid4()).won)
        self.assertEqual(FrontierProgress.objects.get(profile=self.p).unlocked,3)
        self.assertEqual(list(board(self.p.world))[0]['points'],30)
    def test_patrol_loss_and_rollback(self):
        self.finish();self.p.strength=10;self.p.current_health=10;self.p.save()
        row=patrol(self.p,1,uuid4());self.assertFalse(row.won);self.assertEqual(row.snapshot['loot'],[])
        self.p.refresh_from_db();self.assertEqual((self.p.current_energy,self.p.current_health),(80,1))
        self.assertEqual(FrontierProgress.objects.get(profile=self.p).unlocked,1)
        FrontierProgress.objects.filter(profile=self.p).update(last_attempt_at=timezone.now()-timedelta(minutes=6))
        self.p.current_health=1000;self.p.strength=300;self.p.save()
        before=(self.p.ore_balance,self.p.experience,self.p.inventory.count())
        with patch('characters.frontier.FrontierRecord.objects.create',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):patrol(self.p,1,uuid4())
        self.p.refresh_from_db();self.assertEqual(before,(self.p.ore_balance,self.p.experience,self.p.inventory.count()))
        self.assertEqual(FrontierRecord.objects.count(),1)
    def test_forms_csrf_forgeries_and_new_month_keeps_items(self):
        self.assertEqual(self.client.get('/warty/').status_code,200)
        self.assertContains(self.client.get('/ekwipunek/'),'Kuźnia magicznej rudy')
        self.client.post('/ekwipunek/',{'action':'improve','item_id':self.gear.pk,'expected_level':0,'request_key':'invalid','ore':999999})
        self.gear.refresh_from_db();self.assertEqual(self.gear.upgrade_level,0)
        self.finish();patrol(self.p,1,uuid4())
        with patch('characters.frontier.season_key',return_value='2099-01'):self.assertEqual(list(board(self.p.world)),[])
        self.assertEqual(FrontierProgress.objects.get(profile=self.p).unlocked,2)
        self.assertTrue(self.p.inventory.filter(pk=self.gear.pk).exists())
    def test_bot_uses_same_upgrade_and_patrol_services_and_replay(self):
        from .bots import tick_bot
        from .bot_telemetry import replay_decision
        from .models import BotDecision
        self.finish();self.p.is_bot=True;self.p.save();game.equip_item(self.p,self.gear)
        action,ok=tick_bot(self.p, force_active=True);self.assertEqual((action,ok),('improve',True))
        self.assertTrue(replay_decision(BotDecision.objects.first())['matches'])
        self.p.inventory.filter(blueprint__catalog_key='rune-dust').delete()
        action,ok=tick_bot(self.p, force_active=True);self.assertEqual((action,ok),('patrol',True))
        self.assertEqual(self.p.patrols.count(),1)
    def test_bot_reserves_dust_and_does_not_replace_improved_armor_with_weaker_drop(self):
        from .bots import tick_bot
        self.finish();self.p.is_bot=True;self.p.save();game.equip_item(self.p,self.gear)
        armor=add_item(self.p,ItemBluePrint.objects.get(catalog_key='colony-loot-0-armor'),rarity=4)
        armor.upgrade_level=2;armor.save();game.equip_item(self.p,armor)
        weaker=add_item(self.p,ItemBluePrint.objects.get(catalog_key='colony-loot-1-armor'))
        action,ok=tick_bot(self.p, force_active=True)
        self.assertTrue(ok);weaker.refresh_from_db();self.assertFalse(weaker.is_equipped)
        self.dust.refresh_from_db();self.assertFalse(self.dust.is_market_listed)
        # Even an external policy cannot list a material reserved by the ordinary allowlist.
        class DumpDust:
            def choose(policy,observation):return 'list',self.dust.pk
        self.assertEqual(tick_bot(self.p,DumpDust(), force_active=True),('rejected',False))

    def test_population_100_and_validator_301(self):
        from .world_management import WorldSettingsForm
        call_command('run_bots',create=100,create_only=True,limit=100,stdout=StringIO())
        bots=list(PlayerProfile.objects.filter(is_bot=True).select_related('user'))
        self.assertEqual(len(bots),100);self.assertEqual(len({p.display_name for p in bots}),100)
        self.assertTrue(all(not p.user.has_usable_password() for p in bots))
        self.assertTrue(WorldSettingsForm({'name':'Kolonia','bot_count':300}).is_valid())
        self.assertFalse(WorldSettingsForm({'name':'Kolonia','bot_count':301}).is_valid())
        with transaction.atomic():
            with self.assertRaises(IntegrityError):World.objects.filter(pk=self.p.world_id).update(bot_count=301)


class SchedulerTests(SimpleTestCase):
    def test_fairness_pacing_no_catchup_and_refresh(self):
        from .bot_scheduler import BotScheduler
        clock=[0.];scheduler=BotScheduler(interval=5,clock=lambda:clock[0]);scheduler.population(range(1,101));seen=[]
        def tick(pk):seen.append(pk);clock[0]+=.01;return 'mine',True
        for _ in range(100):
            clock[0]=max(clock[0],scheduler.next_tick);scheduler.step(tick)
        self.assertEqual(seen,list(range(1,101)));self.assertGreaterEqual(clock[0],20)
        clock[0]+=1000;scheduler.step(tick);self.assertIsNone(scheduler.step(tick))
        scheduler.population([99,100,101]);self.assertEqual(set(scheduler.queue),{99,100,101})
    def test_rest_backoff_and_expensive_actions_adapt_gap(self):
        from .bot_scheduler import BotScheduler
        clock=[0.];scheduler=BotScheduler(1,lambda:clock[0]);scheduler.population([1])
        def tick(pk):clock[0]+=.5;return 'wait',True
        scheduler.step(tick);self.assertGreaterEqual(scheduler.gap,2)
        clock[0]=scheduler.next_tick;self.assertIsNone(scheduler.step(tick));self.assertGreaterEqual(scheduler.next_tick,30)
