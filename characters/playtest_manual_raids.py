"""Prepared post-campaign water mage earns guild10 through paid manual sorties."""
from datetime import datetime,timedelta
from io import StringIO
from unittest.mock import patch
from uuid import uuid4
from django.core.management import call_command
from django.test import TestCase
from .test_manual_camp_raids import captain
from .camp_raids import rally_manual_raid,strike_camp_raid,claim_camp_raid
from .magic import learn_circle,purchase_magic,prepare_magic,combat_plan
from .models import ItemBluePrint,CampGuild,CampRaid
from . import game_logic as game
from .world_clock import POLISH_TIME
from .release_probe import record_scenario


class ManualGuildRush(TestCase):
    def test_water_archmage_can_earn_guild_ten_without_waiting_for_daily_reset(self):
        now=start=datetime(2026,11,14,9,tzinfo=POLISH_TIME)
        with patch('django.utils.timezone.now',side_effect=lambda:now):
            from .world_management import seed_clean_world
            seed_clean_world()
            p=captain('manual-water','NEW_CAMP','ARCH_WATER')
            p.strength=25;p.experience=250*p.level*(p.level+1)
            p.mana=180;p.current_mana=180;p.weapon_prot=35;p.life=1200;p.current_health=1200
            p.skill_points=105;p.ore_balance=5000;p.save()
            for _ in range(6):self.assertTrue(learn_circle(p))
            bp=ItemBluePrint.objects.get(catalog_key='oe-water-g1-chainlightning-rune')
            rune=purchase_magic(p,bp.pk);self.assertTrue(rune);self.assertTrue(prepare_magic(p,rune.pk))
            guild=CampGuild.objects.get(world=p.world,camp=p.camp)
            self.assertEqual((guild.level,guild.experience),(1,0))
            victories=0;sorties=0;casts=0;energy=0;mana=0;checkpoints=[]
            for wave in range(20):
                guild.refresh_from_db()
                if guild.level==10:break
                request=uuid4();raid=rally_manual_raid(p,request);self.assertTrue(raid)
                self.assertEqual(rally_manual_raid(p,request).pk,raid.pk)
                for _ in range(10):
                    raid.refresh_from_db()
                    if raid.completed_at:break
                    p.refresh_from_db();game.refresh_player(p);plan=combat_plan(p)
                    # Conservative full-rune cost for at most three real rounds.
                    per_cast=max(1,plan.spell.damage-raid.protection//2)
                    needed=min(3,(raid.health+per_cast-1)//per_cast)*plan.cost
                    last=raid.strikes.filter(profile=p).first()
                    seconds=max(0,(20-p.current_energy)*60,(needed-p.current_mana)*30,(10-p.current_health)*60,
                                60-(now-last.created_at).total_seconds() if last else 0)
                    if seconds>0:now+=timedelta(seconds=int(seconds)+1)
                    p.refresh_from_db();game.refresh_player(p)
                    self.assertGreaterEqual(p.current_mana,needed)
                    key=uuid4();strike=strike_camp_raid(p,raid.pk,key);self.assertTrue(strike)
                    self.assertEqual(strike_camp_raid(p,raid.pk,key).pk,strike.pk)
                    sorties+=1;casts+=strike.casts;mana+=strike.mana_cost;energy+=20
                    now+=timedelta(seconds=10)
                raid.refresh_from_db();self.assertEqual(raid.health,0)
                self.assertTrue(claim_camp_raid(p,raid.pk));self.assertTrue(claim_camp_raid(p,raid.pk))
                victories+=1;guild.refresh_from_db()
                checkpoints.append({'victory':victories,'guild_level':guild.level,'guild_xp':guild.experience,'world_hours':round((now-start).total_seconds()/3600,3)})
            self.assertEqual((guild.level,guild.experience,guild.treasury),(10,900,1500))
            self.assertEqual(victories,15);self.assertFalse(rally_manual_raid(p,uuid4()))
            self.assertFalse(CampRaid.objects.exclude(cycle='manual').exists())
            p.refresh_from_db();self.assertEqual(p.premium_balance,15)
            self.assertEqual(mana,casts*16)
            record_scenario('prepared-water-archmage-manual-guild10',{
                'success':True,'initial_character':'Prepared level35 Water Archmage, mana180, protection35, 5000ore/105LP.',
                'ordinary_circle_learning':6,'paid_rune':'oe-water-g1-chainlightning-rune',
                'guild_start_level':1,'guild_end_level':10,'guild_xp':guild.experience,'guild_treasury':guild.treasury,
                'victories':victories,'sorties':sorties,'casts':casts,'energy_spent':energy,'mana_spent':mana,
                'world_hours':round((now-start).total_seconds()/3600,3),'checkpoints':checkpoints,
                'free_runtime_grants':False,'itemshop_refills':0,'scroll_purchases':0,
                'daily_reset_required':False,'global_sleeper_requirements_unchanged':True,
                'limits':['Prepared post-campaign character; not a fresh character walkthrough.',
                          'Virtual clock and known strategy; not human active playtime.',
                          'Solo guild progression only, not the global Sleeper victory; normal resource regeneration.'],
            })
