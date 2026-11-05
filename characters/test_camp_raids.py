from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from .models import CampGuild,CampRaid,CampRaidStrike,CampRaidReward,ItemBluePrint,OwnedItem
from .camp_raids import rally_camp_raid,strike_camp_raid,claim_camp_raid,raid_card
from .magic import prepare_magic

class CampRaidTests(TestCase):
    def setUp(self):
        self.player=User.objects.create_user('first').playerprofile
        self.player.camp='OLD_CAMP';self.player.level=10;self.player.life=200;self.player.current_health=200;self.player.strength=50;self.player.save()
        self.ally=User.objects.create_user('second').playerprofile
        self.ally.camp='OLD_CAMP';self.ally.level=10;self.ally.life=200;self.ally.current_health=200;self.ally.strength=50;self.ally.save()
        self.enemy=User.objects.create_user('other-camp').playerprofile
        self.enemy.camp='NEW_CAMP';self.enemy.level=10;self.enemy.save()
        self.raid=rally_camp_raid(self.player)
    def test_shared_hp_retry_and_cross_camp_isolation(self):
        self.assertEqual(rally_camp_raid(self.ally).pk,self.raid.pk)
        key=uuid4();first=strike_camp_raid(self.player,self.raid.pk,key)
        self.assertGreater(first.damage,0);self.raid.refresh_from_db();hp=self.raid.health
        self.assertEqual(strike_camp_raid(self.player,self.raid.pk,key).pk,first.pk)
        self.raid.refresh_from_db();self.player.refresh_from_db();self.assertEqual(self.raid.health,hp);self.assertEqual(self.player.current_energy,80)
        self.assertFalse(strike_camp_raid(self.enemy,self.raid.pk,uuid4()))
        self.assertTrue(strike_camp_raid(self.ally,self.raid.pk,uuid4()))
        self.raid.refresh_from_db();self.assertLess(self.raid.health,hp)
        self.assertFalse(strike_camp_raid(self.player,self.raid.pk,uuid4()))
    def test_last_blow_caps_damage_and_awards_camp_and_participant_once(self):
        self.raid.health=2;self.raid.save()
        first=strike_camp_raid(self.player,self.raid.pk,uuid4());self.assertEqual(first.damage,2)
        guild=CampGuild.objects.get(camp='OLD_CAMP');self.assertEqual((guild.experience,guild.treasury),(60,100))
        self.assertFalse(strike_camp_raid(self.ally,self.raid.pk,uuid4()))
        self.assertFalse(claim_camp_raid(self.ally,self.raid.pk))
        self.assertTrue(claim_camp_raid(self.player,self.raid.pk));self.assertTrue(claim_camp_raid(self.player,self.raid.pk))
        self.player.refresh_from_db();self.assertEqual((self.player.ore_balance,self.player.experience,self.player.premium_balance),(60,50,1))
        self.assertEqual(CampRaidReward.objects.count(),1)
        guild.refresh_from_db();self.assertEqual(guild.experience,60)
    def test_phase_transition_loss_and_rollback_leave_truthful_logs(self):
        self.raid.health=370;self.raid.save()
        strike=strike_camp_raid(self.player,self.raid.pk,uuid4())
        self.assertTrue(any('szał' in line for line in strike.log))
        self.raid.refresh_from_db();hp=self.raid.health
        with patch.object(CampRaidStrike.objects,'create',side_effect=RuntimeError('Nieudany zapis')):
            with self.assertRaises(RuntimeError):strike_camp_raid(self.ally,self.raid.pk,uuid4())
        self.raid.refresh_from_db();self.ally.refresh_from_db();self.assertEqual(self.raid.health,hp);self.assertEqual(self.ally.current_energy,100)
        self.raid.attack=1000;self.raid.save()
        loss=strike_camp_raid(self.ally,self.raid.pk,uuid4());self.ally.refresh_from_db()
        self.assertEqual(self.ally.current_health,1);self.assertGreater(loss.damage,0)
        self.assertTrue(any('Wycofujesz' in line for line in loss.log))
    def test_mana_scroll_and_no_resource_gate(self):
        bp=ItemBluePrint.objects.create(name='Zwój testowy',kind='scroll',catalog_key='g1-itarscrollfireball')
        scroll=OwnedItem.objects.create(owner=self.player,blueprint=bp,quantity=2)
        self.assertTrue(prepare_magic(self.player,scroll.pk))
        self.player.current_mana=0;self.player.mana_updated_at=timezone.now();self.player.save()
        self.assertFalse(strike_camp_raid(self.player,self.raid.pk,uuid4()))
        self.player.current_mana=2;self.player.save()
        strike=strike_camp_raid(self.player,self.raid.pk,uuid4());self.assertEqual((strike.casts,strike.mana_cost),(2,2))
        self.assertFalse(OwnedItem.objects.filter(pk=scroll.pk).exists())
        self.player.refresh_from_db();self.assertIsNone(self.player.prepared_magic_id)
    def test_reward_failure_rolls_back_and_past_reward_survives_day_reset(self):
        self.raid.health=1;self.raid.save();strike_camp_raid(self.player,self.raid.pk,uuid4())
        with patch('characters.economy.change_premium',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):claim_camp_raid(self.player,self.raid.pk)
        self.assertFalse(CampRaidReward.objects.exists())
        self.player.refresh_from_db();self.assertEqual(self.player.experience,0)
        with patch('django.utils.timezone.now',return_value=timezone.now()+timedelta(days=1)):
            new=rally_camp_raid(self.player);self.assertNotEqual(new.pk,self.raid.pk)
            self.assertEqual(new.health,new.maximum_health)
            self.assertTrue(claim_camp_raid(self.player,self.raid.pk))
    def test_bot_uses_same_strike_service_and_ui_does_not_expose_other_camp(self):
        from .bots import tick_bot
        self.player.is_bot=True;self.player.bot_turn=13;self.player.save()
        action,success=tick_bot(self.player);self.assertEqual((action,success),('raid_strike',True))
        self.assertTrue(CampRaidStrike.objects.filter(profile=self.player).exists())
        self.client.force_login(self.enemy.user)
        response=self.client.post('/wspolnota/',{'action':'strike','raid':self.raid.pk,'request_key':uuid4()})
        self.assertEqual(response.status_code,302)
        self.assertFalse(CampRaidStrike.objects.filter(profile=self.enemy).exists())
        self.assertFalse(raid_card(self.enemy)['raid'])
