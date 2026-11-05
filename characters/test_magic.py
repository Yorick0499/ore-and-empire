from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from uuid import uuid4
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from .models import ItemBluePrint,OwnedItem,BattleRecord,BotDecision
from .magic import BY_KEY,BY_CODE,MagicPlan,prepare_magic,purchase_magic,learn_circle,combat_plan,survival_health
from . import game_logic as game
from .bots import tick_bot,Observation,BaselinePolicy

class MagicTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_catalog',stdout=StringIO())
    def setUp(self):
        self.profile=User.objects.create_user('caster').playerprofile
        self.profile.camp='OLD_CAMP';self.profile.guild='FIRE_MAGE';self.profile.level=15
        self.profile.mana=40;self.profile.current_mana=40;self.profile.life=200;self.profile.current_health=200
        self.profile.ore_balance=5000;self.profile.skill_points=100;self.profile.save()
    def item(self,key='firebolt',scroll=False,owner=None,quantity=1):
        bp=ItemBluePrint.objects.get(catalog_key='g1-itar'+('scroll' if scroll else 'rune')+key)
        return OwnedItem.objects.create(owner=owner or self.profile,blueprint=bp,quantity=quantity)
    def test_circle_cost_rank_level_and_school_gates(self):
        self.assertTrue(learn_circle(self.profile));self.profile.refresh_from_db()
        self.assertEqual((self.profile.magic_skill,self.profile.skill_points,self.profile.ore_balance),(1,95,4950))
        own=self.item();self.assertTrue(prepare_magic(self.profile,own.pk))
        self.assertFalse(prepare_magic(self.profile,self.item('thunderbolt').pk))
        self.assertFalse(prepare_magic(self.profile,self.item('fireball').pk))
        self.profile.guild='SHADOW';self.profile.magic_skill=2;self.profile.save()
        self.assertFalse(learn_circle(self.profile))
        self.profile.guild='FIRE_MAGE';self.profile.magic_skill=4;self.profile.save()
        self.assertFalse(learn_circle(self.profile))
        self.profile.guild='ARCH_FIRE';self.profile.save();self.assertTrue(learn_circle(self.profile))
    def test_purchase_and_prepare_reject_foreign_listed_unsupported_and_resource_spoofing(self):
        other=User.objects.create_user('other').playerprofile
        self.assertFalse(prepare_magic(self.profile,self.item(owner=other).pk))
        listed=self.item(scroll=True);listed.is_market_listed=True;listed.market_price=2;listed.save()
        self.assertFalse(prepare_magic(self.profile,listed.pk))
        bp=ItemBluePrint.objects.get(catalog_key='g1-itarrunefirebolt')
        self.assertFalse(purchase_magic(self.profile,bp.pk))
        self.assertTrue(learn_circle(self.profile))
        before=self.profile.ore_balance
        self.assertTrue(purchase_magic(self.profile,bp.pk));self.profile.refresh_from_db()
        self.assertEqual(self.profile.ore_balance,before-bp.base_value)
        self.client.force_login(self.profile.user)
        self.assertContains(self.client.get('/magia/'),'Kręgi magii')
        self.assertContains(self.client.get('/przedmioty/?q=Ognisty+pocisk'),'Obsługiwane zaklęcie')
    def test_mana_regeneration_preserves_fraction_and_gear_removal_does_not_refill(self):
        now=timezone.now();self.profile.current_mana=1;self.profile.mana_updated_at=now-timedelta(seconds=75);self.profile.save()
        with patch('characters.game_logic.timezone.now',return_value=now):game.refresh_player(self.profile)
        self.assertEqual(self.profile.current_mana,3);self.assertEqual(self.profile.mana_updated_at,now-timedelta(seconds=15))
        ring=ItemBluePrint.objects.create(name='Mana band',kind='ring',mana_bonus=20)
        owned=OwnedItem.objects.create(owner=self.profile,blueprint=ring)
        self.assertTrue(game.equip_item(self.profile,owned));self.profile.refresh_from_db()
        self.assertEqual((self.profile.max_mana,self.profile.current_mana),(60,3))
        self.profile.current_mana=59;self.profile.save();self.assertTrue(game.unequip_item(self.profile,owned))
        self.profile.refresh_from_db();self.assertEqual((self.profile.max_mana,self.profile.current_mana),(40,40))
    def test_rune_and_scroll_costs_and_retry_are_exactly_once(self):
        self.profile.magic_skill=1;self.profile.save();rune=self.item()
        self.assertTrue(prepare_magic(self.profile,rune.pk));key=uuid4()
        first=game.execute_hunt(self.profile,'young_scavenger','forest',key)
        self.profile.refresh_from_db();self.assertEqual(self.profile.current_mana,36)
        self.assertEqual(BattleRecord.objects.get().combat_details['casts'],1)
        self.assertEqual(game.execute_hunt(self.profile,'young_scavenger','forest',key),first)
        self.profile.refresh_from_db();self.assertEqual(self.profile.current_mana,36)
        scroll=self.item('fireball',scroll=True,quantity=2);self.assertTrue(prepare_magic(self.profile,scroll.pk))
        second=uuid4();self.assertTrue(game.execute_hunt(self.profile,'young_scavenger','forest',second))
        scroll.refresh_from_db();self.assertEqual(scroll.quantity,1)
        self.assertTrue(game.execute_hunt(self.profile,'young_scavenger','forest',second));scroll.refresh_from_db();self.assertEqual(scroll.quantity,1)
    def test_no_mana_rejects_without_energy_or_scroll_cost_and_empty_scroll_clears_focus(self):
        scroll=self.item(scroll=True);self.assertTrue(prepare_magic(self.profile,scroll.pk))
        self.profile.current_mana=0;self.profile.mana_updated_at=timezone.now();self.profile.save()
        self.assertFalse(game.execute_hunt(self.profile,'young_scavenger'));self.profile.refresh_from_db()
        self.assertEqual(self.profile.current_energy,100);self.assertTrue(OwnedItem.objects.filter(pk=scroll.pk).exists())
        self.profile.current_mana=1;self.profile.save();self.assertTrue(game.execute_hunt(self.profile,'young_scavenger'))
        self.profile.refresh_from_db();self.assertIsNone(self.profile.prepared_magic_id);self.assertEqual(self.profile.current_mana,0)
    def test_spell_resistances_mitigation_stagger_and_fallback_match_forecast(self):
        monster={'nazwa':'Training target','life':90,'strength':20,'weapon_prot':0,'fire_prot':0,'magic_prot':0}
        for key in ('firebolt','thunderbolt','windfist'):
            plan=MagicPlan(BY_KEY[key],1,False,1)
            with patch('characters.game_logic.random.randint',return_value=100):result=game.simulate_combat(self.profile,'target',monster=monster,magic_plan=plan)
            self.assertTrue(result.won)
            self.assertEqual(self.profile.current_health-result.remaining_health,survival_health(self.profile,monster,plan)-10)
        fire=MagicPlan(BY_KEY['firebolt'],1,False,1)
        resistant={**monster,'fire_prot':23}
        normal=game.simulate_combat(self.profile,'target',monster=monster,magic_plan=fire)
        protected=game.simulate_combat(self.profile,'target',monster=resistant,magic_plan=fire)
        self.assertLess(protected.remaining_health,normal.remaining_health)
        self.assertGreaterEqual(protected.remaining_mana,0)
    def test_battle_failure_rolls_back_mana_scroll_and_rewards(self):
        scroll=self.item(scroll=True);prepare_magic(self.profile,scroll.pk)
        with patch('characters.loot.save_battle',side_effect=RuntimeError('write failed')):
            with self.assertRaises(RuntimeError):game.execute_hunt(self.profile,'young_scavenger')
        self.profile.refresh_from_db();self.assertEqual((self.profile.current_mana,self.profile.current_energy),(40,100))
        self.assertTrue(OwnedItem.objects.filter(pk=scroll.pk).exists());self.assertFalse(BattleRecord.objects.exists())
    def test_mage_bot_learns_buys_prepares_and_casts_through_services(self):
        self.profile.is_bot=True;self.profile.bot_role='hunter';self.profile.save()
        call_command('seed_world',stdout=StringIO())
        actions=[]
        for _ in range(9):
            action,success=tick_bot(self.profile);actions.append(action)
        self.assertIn('learn_circle',actions);self.assertIn('buy_magic',actions);self.assertIn('prepare_magic',actions)
        # Force a known safe combat plan while retaining the ordinary action allowlist.
        class HuntPolicy:
            def choose(self,o):return ('hunt',None) if o.hunt_key else ('wait',None)
        self.profile.refresh_from_db();self.profile.current_energy=100;self.profile.current_health=200;self.profile.save()
        owned=self.profile.inventory.filter(blueprint__kind='rune').first()
        self.assertTrue(prepare_magic(self.profile,owned.pk))
        action,success=tick_bot(self.profile,HuntPolicy());self.assertEqual(action,'hunt');self.assertTrue(success)
        fact=BotDecision.objects.first();self.assertEqual(fact.policy_version,'external-unknown')
        self.assertTrue(BattleRecord.objects.filter(profile=self.profile,combat_details__casts__gt=0).exists())

    def test_three_schools_and_warrior_have_explicit_matchup_tradeoffs(self):
        warrior=User.objects.create_user('warrior').playerprofile
        warrior.strength=40;warrior.life=200;warrior.current_health=200;warrior.save()
        target={'nazwa':'Arena','life':100,'strength':20,'weapon_prot':15,'fire_prot':0,'magic_prot':0}
        results={}
        with patch('characters.game_logic.random.randint',return_value=100):
            results['warrior']=game.simulate_combat(warrior,'arena',monster=target)
            for key in ('fireball','icecube','stormfist'):
                results[key]=game.simulate_combat(self.profile,'arena',monster=target,magic_plan=MagicPlan(BY_KEY[key],1,False,1))
            fire_resistant={**target,'fire_prot':54}
            poor_fire=game.simulate_combat(self.profile,'arena',monster=fire_resistant,magic_plan=MagicPlan(BY_KEY['fireball'],1,False,1))
        self.assertTrue(all(r.won for r in results.values()))
        self.assertEqual({k:r.remaining_health for k,r in results.items()},{'warrior':140,'fireball':180,'icecube':176,'stormfist':180})
        self.assertEqual({k:r.remaining_mana for k,r in results.items() if k!='warrior'},{'fireball':24,'icecube':19,'stormfist':19})
        self.assertFalse(poor_fire.won)

    def test_martial_promotion_clears_an_outgrown_novice_focus(self):
        from .magic import bot_magic_plan
        self.profile.camp='SWAMP_CAMP';self.profile.guild='SWAMP_GUARD';self.profile.magic_skill=2;self.profile.save()
        item=self.item('windfist');self.assertTrue(prepare_magic(self.profile,item.pk))
        self.assertEqual(bot_magic_plan(self.profile,list(self.profile.inventory.select_related('blueprint'))),('clear_magic',None))

    def test_boss_magic_cost_and_durable_retry_use_the_same_result(self):
        self.profile.magic_skill=3;self.profile.save()
        rune=self.item('fireball');self.assertTrue(prepare_magic(self.profile,rune.pk))
        key=uuid4();attempt=game.execute_boss(self.profile,'crawler_nest',key)
        self.assertTrue(attempt.won);self.profile.refresh_from_db()
        mana=self.profile.current_mana;energy=self.profile.current_energy
        self.assertLess(mana,40)
        repeated=game.execute_boss(self.profile,'crawler_nest',key)
        self.assertEqual(repeated.pk,attempt.pk);self.profile.refresh_from_db()
        self.assertEqual((self.profile.current_mana,self.profile.current_energy),(mana,energy))
        self.assertEqual(BattleRecord.objects.get().combat_details['magic'],'fireball')

    def test_each_school_can_prepare_its_rune_and_win_a_paid_hunt(self):
        for camp,guild,key,cost in [('OLD_CAMP','FIRE_MAGE','firebolt',4),('NEW_CAMP','WATER_MAGE','thunderbolt',4),('SWAMP_CAMP','GURU','windfist',3)]:
            self.profile.camp=camp;self.profile.guild=guild;self.profile.magic_skill=1;self.profile.save()
            rune=self.item(key);self.assertTrue(prepare_magic(self.profile,rune.pk))
            before=self.profile.current_mana
            self.assertTrue(game.execute_hunt(self.profile,'young_scavenger'))
            self.profile.refresh_from_db();self.assertEqual(self.profile.current_mana,before-cost)
            self.assertEqual(BattleRecord.objects.first().combat_details['magic'],key)
