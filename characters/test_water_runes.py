"""Paid water-rune progression; no disposable scrolls required for combat."""
from io import StringIO
from unittest.mock import patch
from uuid import uuid4
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from . import game_logic as game
from .bestiary import BESTIARY
from .equipment import add_item
from .magic import (BY_CODE, SPELLS, MagicPlan, bot_magic_plan, combat_plan,
                    learn_circle, offers, prepare_magic, purchase_magic, survival_health)
from .models import ItemBluePrint


class WaterRuneTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from .world_management import seed_clean_world
        seed_clean_world()

    def setUp(self):
        self.p=User.objects.create_user('water-student').playerprofile
        self.p.camp='NEW_CAMP';self.p.guild='ROGUE';self.p.level=30
        self.p.skill_points=200;self.p.ore_balance=10000
        self.p.mana=150;self.p.current_mana=150;self.p.life=500;self.p.current_health=500
        self.p.save()

    def blueprint(self,circle):
        return next(row['blueprint'] for row in offers(self.p)
                    if not row['scroll'] and row['spell'].school=='water' and row['spell'].circle==circle)

    def test_each_circle_has_a_paid_reusable_rune_with_normal_gates(self):
        for circle in range(1,7):
            with self.subTest(circle=circle):
                self.p.guild='ROGUE' if circle<=2 else 'WATER_MAGE' if circle<=4 else 'ARCH_WATER'
                self.p.save()
                ore,points=self.p.ore_balance,self.p.skill_points
                self.assertTrue(learn_circle(self.p))
                self.assertEqual((self.p.ore_balance,self.p.skill_points),(ore-50*circle,points-5*circle))
                bp=self.blueprint(circle)
                before=self.p.ore_balance
                rune=purchase_magic(self.p,bp.pk)
                self.assertTrue(rune);self.assertEqual(self.p.ore_balance,before-bp.base_value)
                self.assertTrue(prepare_magic(self.p,rune.pk))
                plan=combat_plan(self.p)
                self.assertFalse(plan.scroll);self.assertEqual(plan.spell.circle,circle)
                # Reusing it in paid hunts consumes mana, never the rune.
                before=self.p.current_mana
                request=uuid4()
                self.assertTrue(game.execute_hunt(self.p,'young_scavenger','forest',request))
                self.p.refresh_from_db();rune.refresh_from_db()
                self.assertEqual(rune.quantity,1)
                self.assertEqual(self.p.current_mana,before-plan.cost)
                resources=(self.p.current_mana,self.p.current_energy)
                self.assertTrue(game.execute_hunt(self.p,'young_scavenger','forest',request))
                self.p.refresh_from_db()
                self.assertEqual((self.p.current_mana,self.p.current_energy),resources)
                self.p.current_energy=100;self.p.save(update_fields=['current_energy'])
        self.assertFalse(self.p.inventory.filter(blueprint__kind='scroll').exists())

    def test_mage_can_beat_required_ice_golem_without_scrolls_or_fist_fallback(self):
        self.p.guild='WATER_MAGE';self.p.magic_skill=4;self.p.mana=100;self.p.current_mana=100;self.p.save()
        rune=purchase_magic(self.p,self.blueprint(4).pk)
        self.assertTrue(prepare_magic(self.p,rune.pk));plan=combat_plan(self.p)
        target=BESTIARY['ice_golem']
        legacy=MagicPlan(next(spell for spell in SPELLS if spell.key=='icecube'),0,False,1)
        before=game.simulate_combat(self.p,'ice_golem',magic_plan=legacy)
        result=game.simulate_combat(self.p,'ice_golem',magic_plan=plan)
        self.assertFalse(before.won)
        self.assertTrue(result.won)
        damage=plan.spell.damage-target.get('magic_prot',0)
        self.assertGreater(damage,50)
        casts=(target['life']+damage-1)//damage
        self.assertEqual(result.spell_casts,casts)
        self.assertEqual(result.remaining_mana,100-casts*plan.cost)
        self.assertEqual(survival_health(self.p,target,plan),self.p.current_health-result.remaining_health+10)
        from .release_probe import record_scenario
        record_scenario('water-promotion-ice-golem',{
            'fixture':'Prepared mage, 100 mana, 500 HP; same target and attributes.',
            'old_third_circle_won':before.won,'new_fourth_circle_won':result.won,
            'damage_after_resistance':damage,'casts':casts,
            'mana_used':100-result.remaining_mana,'health_used':self.p.current_health-result.remaining_health,
            'scrolls':0,'fist_fallback':False,
        })

    def test_training_and_rune_purchase_cannot_bypass_rank_school_or_circle(self):
        bp=self.blueprint(4)
        self.p.magic_skill=2;self.p.save()
        self.assertFalse(learn_circle(self.p));self.assertFalse(purchase_magic(self.p,bp.pk))
        self.p.magic_skill=4;self.p.guild='FIRE_MAGE';self.p.camp='OLD_CAMP';self.p.save()
        self.assertFalse(purchase_magic(self.p,bp.pk))
        foreign=add_item(self.p,bp)
        self.assertFalse(prepare_magic(self.p,foreign.pk))

    def test_old_owned_runes_gain_power_but_unrestricted_scrolls_do_not(self):
        for key,old_damage in [('thunderbolt',20),('icecube',40),('icewave',75)]:
            rune=BY_CODE['g1-itarrune'+key][0]
            scroll=BY_CODE['g1-itarscroll'+key][0]
            self.assertGreater(rune.damage,old_damage)
            self.assertEqual(scroll.damage,old_damage)
        self.assertEqual(BY_CODE['g1-itarrunefireball'][0].damage,55)
        self.assertEqual(BY_CODE['g1-itarrunestormfist'][0].damage,42)

    def test_reseeding_preserves_owned_runes_and_operator_prices(self):
        bp=self.blueprint(4);owned=add_item(self.p,bp)
        bp.base_value=1234;bp.save(update_fields=['base_value'])
        before=ItemBluePrint.objects.count()
        call_command('seed_equipment',stdout=StringIO())
        self.assertEqual(ItemBluePrint.objects.count(),before)
        owned.refresh_from_db();bp.refresh_from_db()
        self.assertEqual(owned.blueprint_id,bp.pk);self.assertEqual(bp.base_value,1234)

    def test_bot_chooses_the_new_intermediate_rune_and_later_nk_upgrade(self):
        self.p.guild='WATER_MAGE';self.p.magic_skill=4;self.p.save()
        action,pk=bot_magic_plan(self.p,[])
        self.assertEqual(action,'buy_magic')
        self.assertEqual(BY_CODE[ItemBluePrint.objects.get(pk=pk).catalog_key][0].circle,4)
        # Equal-circle upgrades must not strand veterans on the first VI rune.
        self.p.guild='ARCH_WATER';self.p.level=40;self.p.magic_skill=6;self.p.save()
        rune=add_item(self.p,self.blueprint(6));prepare_magic(self.p,rune.pk)
        call_command('seed_gothic2_world',stdout=StringIO())
        with patch('characters.magic.rune_allowed',side_effect=lambda p,s:s.school=='water'),patch('characters.magic.source_games',return_value=['GOTHIC_I','GOTHIC_II']):
            action,pk=bot_magic_plan(self.p,list(self.p.inventory.select_related('blueprint')))
        self.assertEqual(action,'buy_magic')
        self.assertEqual(ItemBluePrint.objects.get(pk=pk).catalog_key,'oe-nk-nk_thunderstorm-rune')

    def test_panel_shows_rune_damage_and_reusable_water_path(self):
        self.p.magic_skill=2;self.p.save()
        rune=purchase_magic(self.p,self.blueprint(2).pk);prepare_magic(self.p,rune.pk)
        self.client.force_login(self.p.user)
        response=self.client.get('/magia/')
        self.assertContains(response,'Lodowa lanca')
        self.assertContains(response,'obrażenia 55')
        self.assertContains(response,'każdy z sześciu kręgów')

    def test_bot_does_not_rebuy_a_stronger_owned_rune_when_lower_circle_is_safer(self):
        self.p.guild='ARCH_WATER';self.p.magic_skill=6;self.p.save()
        fifth=add_item(self.p,self.blueprint(5))
        sixth=add_item(self.p,self.blueprint(6))
        prepare_magic(self.p,fifth.pk)
        inventory=list(self.p.inventory.select_related('blueprint'))
        target={'life':1600,'strength':100,'weapon_prot':0}
        action,pk=bot_magic_plan(self.p,inventory,target)
        self.assertEqual((action,pk),('',None))
        self.assertEqual(self.p.inventory.filter(blueprint=sixth.blueprint).count(),1)
