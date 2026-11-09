"""Regression scenarios found during the first full release bug audit."""
from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connection
from django.test import TestCase,Client
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from . import game_logic as game
from .economy import purchase_product
from .equipment import add_item
from .models import (ItemBluePrint, OwnedItem,
                     MarketTrade, PremiumEntry, PersonalChallenge, PlayerProfile)


class TransactionAuditTests(TestCase):
    def setUp(self):
        self.p = User.objects.create_user('audit-player').playerprofile
        self.other = User.objects.create_user('audit-other').playerprofile
        self.bp = ItemBluePrint.objects.create(name='Miecz audytu', damage=12, base_value=20)
        self.item = add_item(self.p, self.bp)

    def test_named_argument_cannot_sell_a_deleted_item_twice(self):
        stale = OwnedItem.objects.get(pk=self.item.pk)
        self.assertTrue(game.sell_item_from_npc(self.p, self.item))
        self.assertFalse(game.sell_item_from_npc(self.p, item=stale))
        self.p.refresh_from_db()
        self.assertEqual(self.p.ore_balance, 60)

    def test_named_argument_cannot_sell_or_equip_an_item_after_ownership_changed(self):
        stale = OwnedItem.objects.get(pk=self.item.pk)
        self.assertTrue(game.list_item_on_market(self.p, self.item, 20))
        self.assertTrue(game.buy_item_on_market(self.other, owned_item=self.item))
        self.assertFalse(game.equip_item(self.p, owned_item=stale))
        self.assertFalse(game.sell_item_from_npc(self.p, item=stale))
        self.item.refresh_from_db()
        self.assertEqual(self.item.owner_id, self.other.pk)
        self.assertFalse(self.item.is_equipped)

    def test_npc_purchase_refreshes_price_and_availability_of_retained_blueprint(self):
        stale = ItemBluePrint.objects.get(pk=self.bp.pk)
        ItemBluePrint.objects.filter(pk=self.bp.pk).update(base_value=40)
        self.assertTrue(game.buy_item_from_npc(self.p, item=stale))
        self.p.refresh_from_db()
        self.assertEqual(self.p.ore_balance, 10)
        ItemBluePrint.objects.filter(pk=self.bp.pk).update(merchant=False)
        self.assertFalse(game.buy_item_from_npc(self.p, stale))

    def test_named_purchase_replay_and_failure_roll_back_both_accounts(self):
        game.list_item_on_market(self.p, self.item, 20)
        with patch('characters.game_logic.MarketTrade.objects.create', side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                game.buy_item_on_market(self.other, owned_item=self.item)
        self.p.refresh_from_db(); self.other.refresh_from_db(); self.item.refresh_from_db()
        self.assertEqual((self.p.ore_balance, self.other.ore_balance), (50, 50))
        self.assertTrue(self.item.is_market_listed)
        self.assertTrue(game.buy_item_on_market(self.other, owned_item=self.item))
        self.assertFalse(game.buy_item_on_market(self.other, owned_item=self.item))
        self.assertEqual(MarketTrade.objects.count(), 1)

    def test_deleted_npc_blueprint_is_rejected_instead_of_charging_or_crashing(self):
        bp=ItemBluePrint.objects.create(name='Wycofany towar',damage=10,base_value=10)
        stale=ItemBluePrint.objects.get(pk=bp.pk)
        bp.delete()
        self.assertFalse(game.buy_item_from_npc(self.p,item=stale))
        self.p.refresh_from_db();self.assertEqual(self.p.ore_balance,50)

    def test_challenge_with_zero_premium_still_pays_ore_and_xp_once(self):
        from .challenges import claim_challenge, period_for
        challenge = PersonalChallenge.objects.create(profile=self.p, cadence='daily', period=period_for('daily'), kind='mine', required=1, progress=1, ore=7, experience=10, premium=0, reputation=0)
        self.assertTrue(claim_challenge(self.p, challenge.pk))
        self.assertFalse(claim_challenge(self.p, challenge.pk))
        self.p.refresh_from_db()
        self.assertEqual((self.p.ore_balance, self.p.experience, self.p.premium_balance), (57, 10, 0))
        self.assertFalse(PremiumEntry.objects.exists())


class RangedBotAuditTests(TestCase):
    def setUp(self):
        call_command('seed_world', stdout=StringIO())
        call_command('seed_equipment', stdout=StringIO())
        self.p = User.objects.create_user('audit-ranger').playerprofile
        self.p.is_bot=True; self.p.bot_role='hunter'; self.p.camp='OLD_CAMP'
        self.p.bot_turn=5; self.p.level=3; self.p.dexterity=20; self.p.ore_balance=40
        self.p.save()
        bow=ItemBluePrint.objects.create(name='Łuk audytu', kind='weapon', weapon_type='bow', damage_type='arrow', damage=35, required_dexterity=10)
        self.bow=add_item(self.p,bow); game.equip_item(self.p,self.bow)

    def test_ranged_bot_buys_real_ammo_and_then_can_hunt(self):
        from .bots import tick_bot
        action, success=tick_bot(self.p, force_active=True)
        self.assertTrue(success)
        self.assertTrue(self.p.inventory.filter(blueprint__kind='ammo',blueprint__original_stats__ammo_type='arrow').exists(),action)
        self.assertEqual(self.p.purchases.count(),0)
        self.p.refresh_from_db(); self.assertLess(self.p.ore_balance,40)
        self.assertIsNot(game.execute_hunt(self.p,'young_scavenger','exchange'),False)

    def test_no_ammo_and_no_stock_never_produces_a_failed_combat_decision(self):
        from .bots import tick_bot
        ItemBluePrint.objects.filter(kind='ammo').update(merchant=False)
        start=timezone.now()
        for step in range(30):
            with patch('django.utils.timezone.now',return_value=start+timedelta(minutes=2*step)):
                action,success=tick_bot(self.p, force_active=True)
                self.assertTrue(success,action)

    def test_crossbow_does_not_treat_arrows_or_listed_bolts_as_available_ammo(self):
        from .bots import tick_bot
        self.bow.blueprint.weapon_type='crossbow';self.bow.blueprint.save()
        add_item(self.p,ItemBluePrint.objects.get(catalog_key='g1-arrow'),5)
        bolts=add_item(self.p,ItemBluePrint.objects.get(catalog_key='g1-bolt'),5)
        game.list_item_on_market(self.p,bolts,10)
        action,ok=tick_bot(self.p, force_active=True)
        self.assertEqual((action,ok),('ammo',True))
        self.assertEqual(self.p.inventory.get(blueprint__catalog_key='g1-bolt',is_market_listed=False).quantity,1)

    def test_ranged_forecast_uses_dexterity_instead_of_high_strength(self):
        from .bots import tick_bot,health_needed
        from .models import BotDecision
        from .equipment import combat_values
        from .bestiary import BESTIARY
        self.p.strength=100;self.p.current_health=10;self.p.save()
        add_item(self.p,ItemBluePrint.objects.get(catalog_key='g1-arrow'),5)
        _,ok=tick_bot(self.p, force_active=True);self.assertTrue(ok)
        decision=BotDecision.objects.filter(profile=self.p).first()
        key=decision.observation['hunt_key']
        self.assertIsNotNone(key)
        self.assertLessEqual(health_needed(self.p,BESTIARY[key],combat_values(self.p)[0]),10)

    def test_ammo_decision_replays_and_forged_ammo_target_is_rejected(self):
        from .bots import tick_bot
        from .models import BotDecision
        from .bot_telemetry import replay_decision
        self.assertEqual(tick_bot(self.p, force_active=True),('ammo',True))
        fact=BotDecision.objects.filter(profile=self.p).first()
        self.assertTrue(replay_decision(fact)['matches'])
        before=self.p.inventory.count()
        class Forged:
            def choose(self,observation):return 'ammo',999999
        self.assertEqual(tick_bot(self.p,Forged(), force_active=True),('rejected',False))
        self.assertEqual(self.p.inventory.count(),before)

    def test_magic_comparison_includes_physical_armor_against_arrows(self):
        from .magic import bot_magic_plan
        self.p.guild='FIRE_MAGE';self.p.magic_skill=1;self.p.mana=50;self.p.current_mana=50;self.p.save()
        bp=ItemBluePrint.objects.create(catalog_key='g1-itarrunefirebolt',name='Runa audytu',kind='rune',base_value=10)
        rune=add_item(self.p,bp)
        target={'life':100,'strength':30,'weapon_prot':100}
        inventory=list(self.p.inventory.select_related('blueprint'))
        self.assertEqual(bot_magic_plan(self.p,inventory,target),('prepare_magic',rune.pk))

    def test_trader_keeps_ammo_for_own_weapon_instead_of_listing_it_again(self):
        from .bots import tick_bot
        from .models import MarketEvent
        self.p.bot_role='trader';self.p.save()
        add_item(self.p,ItemBluePrint.objects.get(catalog_key='g1-arrow'),5)
        now=timezone.now()
        for step in range(20):
            with patch('django.utils.timezone.now',return_value=now+timedelta(minutes=2*step)):
                action,ok=tick_bot(self.p, force_active=True);self.assertTrue(ok,action)
        self.assertFalse(MarketEvent.objects.filter(profile=self.p,blueprint__kind='ammo',action='listing').exists())


class InventoryQueryAuditTests(TestCase):
    def test_market_and_merchant_do_not_fetch_a_blueprint_per_backpack_item(self):
        user=User.objects.create_user('audit-large-bag');p=user.playerprofile
        bp=ItemBluePrint.objects.create(name='Oręż audytu',damage=12,base_value=20)
        OwnedItem.objects.bulk_create([OwnedItem(owner=p,blueprint=bp) for _ in range(40)])
        self.client.force_login(user)
        for url in ('/plac_targowy/','/sklep/'):
            with self.subTest(url=url):
                with CaptureQueriesContext(connection) as queries:
                    response=self.client.get(url)
                    self.assertEqual(response.status_code,200)
                blueprint_queries=[q for q in queries if 'SELECT' in q['sql'] and '"characters_itemblueprint"' in q['sql']]
                self.assertLessEqual(len(blueprint_queries),5)
                from .release_probe import record_scenario
                record_scenario('audyt-zapytan-plecaka',{'route':url,'items':40,'blueprint_queries':len(blueprint_queries)})


class CampRewardAuditTests(TestCase):
    def test_zero_premium_raid_reward_can_be_claimed(self):
        from .camp_raids import claim_camp_raid
        from .models import CampGuild,CampRaid,CampRaidStrike,CampRaidReward
        p=User.objects.create_user('audit-raid').playerprofile
        p.camp='OLD_CAMP';p.save()
        guild,_=CampGuild.objects.get_or_create(world=p.world,camp=p.camp)
        raid=CampRaid.objects.create(guild=guild,day=timezone.localdate(),name='Próba',maximum_health=10,health=0,attack=1,protection=0,completed_at=timezone.now())
        CampRaidStrike.objects.create(raid=raid,profile=p,request_key=uuid4(),damage=10,health_cost=0)
        # Operators may configure non-premium rewards; zero is a valid schema value.
        original=CampRaidReward.objects.create
        def configured(**kwargs):return original(**kwargs, premium=0)
        with patch('characters.camp_raids.CampRaidReward.objects.create',side_effect=configured):
            self.assertTrue(claim_camp_raid(p,raid.pk))
        self.assertTrue(claim_camp_raid(p,raid.pk))
        self.assertEqual(CampRaidReward.objects.count(),1)
        self.assertFalse(PremiumEntry.objects.exists())


class EndgameFormsAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_equipment',stdout=StringIO())

    def setUp(self):
        from .models import BossAttempt,CampaignCompletion
        self.user=User.objects.create_user('audit-endgame');self.p=self.user.playerprofile
        self.p.level=30;self.p.strength=300;self.p.life=500;self.p.current_health=500
        self.p.ore_balance=10000;self.p.camp='OLD_CAMP';self.p.save()
        battle=BossAttempt.objects.create(profile=self.p,boss_key='sleeper_sanctum',won=True)
        CampaignCompletion.objects.create(profile=self.p,battle=battle)
        self.item=add_item(self.p,ItemBluePrint.objects.get(catalog_key='colony-loot-0-onehand'))
        add_item(self.p,ItemBluePrint.objects.get(catalog_key='rune-dust'),200)
        self.client.force_login(self.user)

    def state(self):
        self.p.refresh_from_db()
        return (self.p.ore_balance,self.p.experience,self.p.current_energy,self.p.current_health,self.p.current_mana,
                list(self.p.inventory.order_by('pk').values_list('pk','quantity','upgrade_level')))

    def test_repeated_forms_never_duplicate_upgrade_or_patrol_rewards(self):
        now=timezone.now()
        with patch('django.utils.timezone.now',return_value=now):
            upgrade={'action':'improve','item_id':self.item.pk,'expected_level':0,'request_key':uuid4()}
            self.assertEqual(self.client.post('/ekwipunek/',upgrade).status_code,302)
            after=self.state()
            for _ in range(10):self.assertEqual(self.client.post('/ekwipunek/',upgrade).status_code,302)
            self.assertEqual(self.state(),after)
            self.item.refresh_from_db();self.assertEqual(self.item.upgrade_level,1)
            patrol={'depth':1,'request_key':uuid4(),'ore':999999,'points':999999}
            self.assertEqual(self.client.post('/warty/',patrol).status_code,302)
            after=self.state()
            for _ in range(10):self.assertEqual(self.client.post('/warty/',patrol).status_code,302)
            self.assertEqual(self.state(),after)
            self.assertEqual(self.p.patrols.count(),1)
            self.assertEqual(self.p.patrols.get().points,10)
            from .release_probe import record_scenario
            record_scenario('audyt-powtorzonych-formularzy',{'upgrade_replays':10,'patrol_replays':10,'upgrades':1,'patrol_records':self.p.patrols.count()})

    def test_foreign_items_locked_depth_and_bad_keys_have_no_effect(self):
        other=User.objects.create_user('audit-owner').playerprofile
        foreign=add_item(other,self.item.blueprint)
        with patch('django.utils.timezone.now',return_value=timezone.now()):
            before=self.state()
            for action in ('improve','salvage'):
                self.assertEqual(self.client.post('/ekwipunek/',{'action':action,'item_id':foreign.pk,'expected_level':0,'request_key':uuid4()}).status_code,302)
            for key in ('invalid','x'*2000):
                self.assertEqual(self.client.post('/ekwipunek/',{'action':'improve','item_id':self.item.pk,'expected_level':0,'request_key':key}).status_code,302)
            self.assertEqual(self.client.post('/warty/',{'depth':100,'request_key':uuid4()}).status_code,302)
            self.assertEqual(self.state(),before)
        foreign.refresh_from_db();self.assertEqual((foreign.owner_id,foreign.upgrade_level),(other.pk,0))
        self.assertFalse(self.p.patrols.exists())

    def test_malformed_ids_and_csrf_rejection_do_not_mutate_game(self):
        routes=[('/ekwipunek/',{'action':'equip','item_id':None}),('/plac_targowy/',{'action':'buy','buy_item_id':None}),('/sklep/',{'action':'sell','sell_item_id':None}),('/warty/',{'depth':None})]
        with patch('django.utils.timezone.now',return_value=timezone.now()):
            before=self.state()
            for url,base in routes:
                field=next(k for k,v in base.items() if v is None)
                for bad in ('','-1','0','9'*200,'1 OR 1=1','<script>'):
                    with self.subTest(url=url,value=bad):
                        self.assertEqual(self.client.post(url,{**base,field:bad}).status_code,404)
            secure=Client(enforce_csrf_checks=True);secure.force_login(self.user)
            for url,data in [('/ekwipunek/',{'action':'improve','item_id':self.item.pk,'expected_level':0,'request_key':uuid4()}),('/warty/',{'depth':1,'request_key':uuid4()})]:
                self.assertEqual(secure.post(url,data).status_code,403)
            self.assertEqual(self.state(),before)
            from .release_probe import record_scenario
            record_scenario('audyt-blednych-identyfikatorow-i-csrf',{'malformed_posts':24,'csrf_rejections':2,'progress_unchanged':True})

    def test_tavern_escapes_player_supplied_markup(self):
        from .community import post_message
        text='<script>alert("audit")</script>'
        topic=post_message(self.p,text,title='Wiadomość audytu')
        response=self.client.get('/karczma/',{'topic':topic.pk})
        self.assertEqual(response.status_code,200)
        self.assertNotContains(response,text)
        self.assertContains(response,'&lt;script&gt;')
