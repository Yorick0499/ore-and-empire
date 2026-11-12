from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.db import transaction,connections,close_old_connections
from django.test import SimpleTestCase,TestCase,TransactionTestCase,skipUnlessDBFeature
from django.utils import timezone
from .models import CampQuest,FactionRankProgress,PlayerProfile,ItemBluePrint,OwnedItem,CampGuild
from .test_faction_succession import fixture,person,succeed
from .faction_advancement import RANKS,BY_KEY,current_tier,advanced_tier,cards
from .camp_progression import accept_camp_quest,promote_in_camp,record_camp_event
from .factions import FACTIONS,RANK_NAMES


class CatalogTests(SimpleTestCase):
    def test_twenty_advanced_ranks_use_real_targets_and_fit_persisted_keys(self):
        from .bestiary import BESTIARY
        from .bosses import BOSSES
        self.assertEqual(len(RANKS),20)
        for faction,_ in FACTIONS:
            branch=[r for r in RANKS if r.camp==faction]
            self.assertEqual([r.tier for r in branch],[4,5,6,7]);self.assertEqual([r.level for r in branch],[30,35,40,45])
            self.assertEqual([r.name for r in branch],list(RANK_NAMES[faction][4:]))
        for rank in RANKS:
            self.assertLessEqual(len(rank.key),20)
            for goal in rank.objectives:
                kind,_,key=goal.event.partition(':')
                if kind=='hunt':self.assertIn(key,BESTIARY)
                if kind=='boss':self.assertIn(key,BOSSES)

    def test_offline_validator_rejects_missing_advanced_boss(self):
        from dataclasses import replace
        from .camp_progression import obj
        from .management.commands.validate_content import validate_advancements
        fake=replace(RANKS[0],objectives=(obj('boss:missing-boss',1,'Missing'),))
        with patch('characters.faction_advancement.RANKS',(fake,)):
            with self.assertRaisesRegex(ValueError,'Unknown rank boss'):validate_advancements()


class PromotionPolicyTests(SimpleTestCase):
    def test_new_priority_does_not_change_historical_replay(self):
        from dataclasses import asdict
        from types import SimpleNamespace
        from .bots import Observation,BaselinePolicy,BaselinePolicyV21
        from .bot_telemetry import replay_decision
        o=Observation(energy=100,ore=1000,busy=False,reward_ready=False,offer_id=None,inventory_id=99,blueprint_id=None,equip_id=None,armed=True,rank_action='accept',rank_target=31)
        self.assertEqual(BaselinePolicy().choose(o),('accept',31))
        self.assertEqual(BaselinePolicyV21().choose(o),('list',99))
        for version,action,target in [('baseline-21','list',99),('baseline-22','accept',31)]:
            result=replay_decision(SimpleNamespace(policy_version=version,observation=asdict(o),action=action,target_id=target))
            self.assertTrue(result['matches'])


class AdvancementTests(TestCase):
    def setUp(self):self.c,self.i,self.race=fixture()
    def veteran(self,camp='OLD_CAMP',rank='BARON',legacy=0):
        p=person(self.i if camp in {'CITY_WATCH','FIRE_ORDER','ONAR_MERCS'} else self.c,camp,rank)
        p.level=45;p.strength=180;p.dexterity=180;p.mana=200;p.life=6000;p.current_health=6000;p.current_energy=100;p.fire_prot=100;p.weapon_prot=100;p.ore_balance=20000;p.alliance_rank=legacy;p.save()
        return p
    def complete(self,p,rank):
        for goal in rank.objectives:
            for _ in range(goal.count):
                with transaction.atomic():record_camp_event(p,goal.event)
    def test_every_faction_advances_four_times_with_one_charge_and_preserved_native_identity(self):
        people=[self.veteran(camp,key) for camp,key in [('OLD_CAMP','BARON'),('OLD_CAMP','ARCH_FIRE'),('NEW_CAMP','ARCH_WATER'),('CITY_WATCH','K2_COMMANDER'),('ONAR_MERCS','K2_CAPTAIN')]]
        succeed(self.race)
        for p in people:
            p.refresh_from_db();native=(p.camp,p.guild);ore=p.ore_balance
            for rank in [r for r in RANKS if r.camp==p.faction_membership.faction]:
                self.assertTrue(accept_camp_quest(p,rank.key));self.assertFalse(accept_camp_quest(p,rank.key))
                self.assertFalse(promote_in_camp(p,rank.key));self.complete(p,rank)
                self.assertTrue(promote_in_camp(p,rank.key));self.assertFalse(promote_in_camp(p,rank.key))
                ore-=rank.cost;p.refresh_from_db()
                self.assertEqual((p.ore_balance,p.camp,p.guild),(ore,*native));self.assertEqual(p.guild_name,rank.name);self.assertEqual(p.camp_tier,rank.tier)
            self.assertEqual(current_tier(p),7)
    def test_rank_gates_reject_foreign_rank_skip_low_level_stat_ore_busy_and_prebarrier(self):
        p=self.veteran();succeed(self.race);p.refresh_from_db();rank=BY_KEY['ADV_BANDITS_4']
        self.assertFalse(accept_camp_quest(p,'ADV_FIRE_ORDER_4'));self.assertFalse(accept_camp_quest(p,'ADV_BANDITS_5'))
        self.assertTrue(accept_camp_quest(p,rank.key));self.complete(p,rank)
        for field,value in [('level',29),('strength',10),('ore_balance',499)]:
            original=getattr(p,field);old_dex=p.dexterity
            setattr(p,field,value)
            if field=='strength':p.dexterity=10
            p.save();self.assertFalse(promote_in_camp(p,rank.key));setattr(p,field,original);p.dexterity=old_dex;p.save()
        p.action_end_time=timezone.now()+timedelta(seconds=60);p.save();self.assertFalse(promote_in_camp(p,rank.key))
        p.action_end_time=None;p.save()
        from .models import World
        World.objects.filter(pk__in=[self.c.pk,self.i.pk]).update(union_key=None)
        self.assertFalse(promote_in_camp(p,rank.key))
    def test_archer_can_qualify_with_dexterity_without_strength_build_conversion(self):
        p=self.veteran();p.strength=10;p.save();succeed(self.race)
        rank=BY_KEY['ADV_BANDITS_4'];self.assertTrue(accept_camp_quest(p,rank.key));self.complete(p,rank)
        self.assertTrue(promote_in_camp(p,rank.key));p.refresh_from_db();self.assertEqual(p.strength,10)
    def test_existing_paid_fifth_alliance_rank_is_relabelled_without_repurchase(self):
        p=self.veteran('NEW_CAMP','MERC',legacy=4);succeed(self.race);p.refresh_from_db()
        self.assertEqual(current_tier(p),4);self.assertEqual(p.guild_name,'Łowca Smoków')
        self.assertFalse(accept_camp_quest(p,'ADV_MERCENARIES_4'))
        self.assertEqual(p.ore_balance,20000);self.assertFalse(FactionRankProgress.objects.exists())
        self.assertTrue(accept_camp_quest(p,'ADV_MERCENARIES_5'))
    def test_paid_fourth_alliance_rank_satisfies_base_without_another_promotion_fee(self):
        p=self.veteran('NEW_CAMP','MERC',legacy=3);succeed(self.race);p.refresh_from_db()
        self.assertEqual(current_tier(p),3);self.assertEqual(p.guild_name,'Kapitan Najemników')
        self.assertTrue(accept_camp_quest(p,'ADV_MERCENARIES_4'));self.assertEqual(p.ore_balance,20000)

    def test_new_join_never_grants_advanced_rank_and_pending_brotherhood_cannot_advance(self):
        p=self.veteran(legacy=0);brother=self.veteran('SWAMP_CAMP','ARCH_GURU');succeed(self.race)
        for actor in [p,brother]:
            actor.refresh_from_db();self.assertIsNone(advanced_tier(actor))
        self.assertEqual(current_tier(p),3);self.assertEqual(cards(brother),[])
    def test_promotion_rolls_back_state_and_debit_if_quest_save_fails(self):
        p=self.veteran();succeed(self.race);rank=BY_KEY['ADV_BANDITS_4'];accept_camp_quest(p,rank.key);self.complete(p,rank)
        with patch.object(CampQuest,'save',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):promote_in_camp(p,rank.key)
        p.refresh_from_db();self.assertEqual(p.ore_balance,20000);self.assertFalse(FactionRankProgress.objects.exists())
    def test_bot_recovers_for_active_rank_hunts_instead_of_farming_easier_fights(self):
        from .bots import tick_bot
        p=self.veteran();p.is_bot=True;p.current_health=1;p.health_updated_at=timezone.now();p.save();succeed(self.race)
        self.assertTrue(accept_camp_quest(p,'ADV_BANDITS_4'))
        seen=[]
        class ObservePolicy:
            def choose(self,o):seen.append(o);return 'wait',None
        self.assertEqual(tick_bot(p,policy=ObservePolicy(),force_active=True),('wait',True))
        self.assertTrue(seen[0].story_recover)
        p.current_health=p.max_health;p.health_updated_at=timezone.now();p.save()
        tick_bot(p,policy=ObservePolicy(),force_active=True)
        self.assertTrue(seen[-1].quest_hunt)

    def test_beginner_sees_future_ranks_collapsed_and_veteran_can_see_next_step(self):
        from django.urls import reverse
        p=self.veteran();succeed(self.race);self.client.force_login(p.user)
        response=self.client.get(reverse('camp_page'));self.assertEqual(response.status_code,200)
        self.assertTrue(response.context['advanced_path_open'])
        self.assertEqual(response.context['advanced_cards'][0]['rank'].key,'ADV_BANDITS_4')
        p.guild='DIGGER';p.save()
        response=self.client.get(reverse('camp_page'));self.assertFalse(response.context['advanced_path_open'])

    def test_actual_mining_hunts_and_bosses_advance_a_prepared_veteran(self):
        from . import game_logic as game
        from .locations import LOCATIONS
        p=self.veteran();succeed(self.race)
        weapon=ItemBluePrint.objects.create(name='Prepared veteran weapon',kind='weapon',weapon_type='onehand',damage=200,source_game='adaptation')
        OwnedItem.objects.create(owner=p,blueprint=weapon,is_equipped=True,equipped_slot='weapon')
        now=timezone.now()
        for rank in [r for r in RANKS if r.camp=='BANDITS']:
            self.assertTrue(accept_camp_quest(p,rank.key))
            for goal in rank.objectives:
                kind,_,target=goal.event.partition(':')
                for _ in range(goal.count):
                    now+=timedelta(hours=2)
                    with patch('django.utils.timezone.now',return_value=now):
                        if kind=='mine':self.assertTrue(game.start_mining(p,15))
                        elif kind=='hunt':
                            location=next(loc for loc in LOCATIONS if target in loc.monsters and loc.accessible(p))
                            self.assertIsNot(game.execute_hunt(p,target,location.key),False)
                            self.assertTrue(p.battles.first().won)
                        else:self.assertTrue(game.execute_boss(p,target).won)
                    if kind=='mine':
                        now+=timedelta(seconds=16)
                        with patch('django.utils.timezone.now',return_value=now):self.assertTrue(game.claim_ore_reward(p))
            with patch('django.utils.timezone.now',return_value=now):self.assertTrue(promote_in_camp(p,rank.key))
        self.assertEqual(current_tier(p),7)
        entries=p.economic_entries.filter(resource='ore',operation='promote_in_camp')
        self.assertEqual(entries.count(),4);self.assertEqual(sum(entries.values_list('amount',flat=True)),-5500)


@skipUnlessDBFeature('has_select_for_update')
class AdvancementContentionTests(TransactionTestCase):
    def test_repeated_promotion_debits_once_and_records_one_tier(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        c,i,race=fixture();p=person(c,'OLD_CAMP','BARON');p.level=30;p.strength=100;p.ore_balance=1000;p.save();succeed(race)
        rank=BY_KEY['ADV_BANDITS_4'];accept_camp_quest(p,rank.key)
        for goal in rank.objectives:
            for _ in range(goal.count):
                with transaction.atomic():record_camp_event(p,goal.event)
        gate=Barrier(2)
        def run(n):
            close_old_connections()
            try:gate.wait(timeout=10);return promote_in_camp(PlayerProfile.objects.get(pk=p.pk),rank.key)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
        self.assertEqual(sum(results),1);p.refresh_from_db();self.assertEqual(p.ore_balance,500)
        self.assertEqual(FactionRankProgress.objects.count(),1)
