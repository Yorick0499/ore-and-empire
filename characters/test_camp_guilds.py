from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from .models import CampGuild,CampProject,CampContribution
from .camp_guilds import current_project,donate_to_camp,upgrade_camp
from . import game_logic as game

class CampGuildTests(TestCase):
    def setUp(self):
        self.player=User.objects.create_user('member').playerprofile;self.player.camp='OLD_CAMP';self.player.ore_balance=500;self.player.skill_points=10;self.player.save()
        self.other=User.objects.create_user('outsider').playerprofile;self.other.camp='NEW_CAMP';self.other.save()
        self.guild=CampGuild.objects.get(camp='OLD_CAMP')
    def test_shared_actions_complete_once_and_never_count_other_camps_or_failed_actions(self):
        project=current_project(self.guild);project.objectives=[{'id':'hunt','kind':'hunt','target':'','count':2}];project.save()
        key=uuid4();self.assertTrue(game.execute_hunt(self.player,'young_scavenger','forest',key))
        self.assertTrue(game.execute_hunt(self.player,'young_scavenger','forest',key))
        self.assertTrue(game.execute_hunt(self.other,'young_scavenger'))
        project.refresh_from_db();self.assertEqual(project.progress,{'hunt':1})
        ally=User.objects.create_user('ally').playerprofile;ally.camp='OLD_CAMP';ally.is_bot=True;ally.save()
        self.assertTrue(game.execute_hunt(ally,'young_scavenger'))
        self.assertTrue(game.execute_hunt(ally,'young_scavenger'))
        self.guild.refresh_from_db();self.assertEqual((self.guild.experience,self.guild.treasury),(30,50))
        self.assertEqual(CampContribution.objects.filter(guild=self.guild).count(),2)
    def test_donation_retry_cost_rollback_and_no_foreign_guild_parameter(self):
        key=uuid4();self.assertTrue(donate_to_camp(self.player,100,key));self.assertTrue(donate_to_camp(self.player,100,key))
        self.assertFalse(donate_to_camp(self.player,101,key));self.player.refresh_from_db();self.assertEqual(self.player.ore_balance,400)
        self.guild.refresh_from_db();self.assertEqual(self.guild.treasury,100)
        self.client.force_login(self.player.user)
        self.client.post('/wspolnota/',{'action':'donate','amount':10,'request_key':uuid4(),'camp':'NEW_CAMP'})
        self.assertEqual(CampGuild.objects.get(camp='NEW_CAMP').treasury,0)
        with patch.object(CampContribution.objects,'create',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):donate_to_camp(self.player,10,uuid4())
        self.player.refresh_from_db();self.assertEqual(self.player.ore_balance,390)
    def test_upgrade_is_capped_stale_form_cannot_buy_twice_and_benefits_are_derived(self):
        self.guild.level=4;self.guild.experience=300;self.guild.treasury=1000;self.guild.save()
        self.assertTrue(upgrade_camp(self.player,'training',0));self.assertFalse(upgrade_camp(self.player,'training',0))
        self.assertTrue(game.train_attribute(self.player,'strength'));self.player.refresh_from_db();self.assertEqual(self.player.ore_balance,491)
        self.assertTrue(upgrade_camp(self.player,'defense',0));game.refresh_player(self.player)
        self.assertEqual(self.player.effective_protection(),1);self.assertEqual(self.other.effective_protection(),0)
        self.assertFalse(upgrade_camp(self.player,'unknown',0))
    def test_utc_rotation_no_retroactive_credit_and_anonymous_gate(self):
        now=timezone.now();first=current_project(self.guild,now)
        second=current_project(self.guild,now+timedelta(days=1));self.assertNotEqual(first.pk,second.pk)
        self.assertEqual(second.progress,{})
        self.assertEqual(self.client.get('/wspolnota/').status_code,302)
        self.client.force_login(self.player.user);self.assertContains(self.client.get('/wspolnota/'),'Wspólnota obozu')

    def test_project_failure_rolls_back_battle_guild_reward_and_contribution(self):
        from .models import BattleRecord
        project=current_project(self.guild);project.objectives=[{'id':'hunt','kind':'hunt','target':'','count':1}];project.save()
        with patch.object(CampProject,'save',side_effect=RuntimeError('Nieudany zapis projektu')):
            with self.assertRaises(RuntimeError):game.execute_hunt(self.player,'young_scavenger')
        self.player.refresh_from_db();self.guild.refresh_from_db()
        self.assertEqual((self.player.current_energy,self.guild.experience,self.guild.treasury),(100,0,0))
        self.assertFalse(CampContribution.objects.exists());self.assertFalse(BattleRecord.objects.exists())

    def test_bot_donates_only_through_regular_allowlisted_action(self):
        from .bots import tick_bot
        self.player.is_bot=True;self.player.bot_turn=17;self.player.save()
        action,success=tick_bot(self.player, force_active=True)
        self.assertEqual((action,success),('camp_donate',True))
        self.player.refresh_from_db();self.assertEqual(self.player.ore_balance,490)
        self.assertEqual(CampContribution.objects.get(profile=self.player).kind,'donation')
