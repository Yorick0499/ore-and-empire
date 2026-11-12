from unittest.mock import patch
from uuid import uuid4
from django.contrib.auth.models import User
from django.db import connection,connections,close_old_connections,transaction
from django.test import TestCase,TransactionTestCase,skipUnlessDBFeature,Client
from django.urls import reverse
from .models import (FactionMembership,FactionChoice,PlayerProfile,CampGuild,CampQuest,
    ItemBluePrint,OwnedItem,World)
from .test_faction_succession import fixture,person,succeed
from .faction_choice import choose,card
from .factions import FACTIONS,RANK_NAMES,enroll
from .camp_progression import BY_RANK,available_rank,promote_in_camp


class ChoiceTests(TestCase):
    def setUp(self):self.c,self.i,self.race=fixture()
    def pending(self,rank='TEMPLAR'):
        p=person(self.c,'SWAMP_CAMP',rank)
        return p
    def join(self):succeed(self.race)
    def test_all_six_ranks_and_unranked_member_have_exact_allowed_destinations(self):
        for rank in ('NONE','PICKER','NOVICE','SWAMP_GUARD','TEMPLAR','GURU','ARCH_GURU'):
            for key,_ in FACTIONS:
                with self.subTest(rank=rank,destination=key):
                    p=self.pending(rank)
                    # Fresh actor added after the external join, enroll through the
                    # same internal adapter used by native promotion/recruitment.
                    self.join()
                    with transaction.atomic():enroll(p)
                    before={f:getattr(p,f) for f in ('level','experience','strength','dexterity','mana','life','ore_balance','skill_points','magic_skill','guild','camp')}
                    allowed=rank not in {'GURU','ARCH_GURU'} or key in {'FIRE_ORDER','WATER_CIRCLE'}
                    self.assertEqual(choose(p,key),allowed)
                    p.refresh_from_db()
                    self.assertEqual(before,{f:getattr(p,f) for f in before})
                    if allowed:
                        self.assertEqual(p.faction_membership.faction,key)
                        self.assertEqual(p.guild_name,RANK_NAMES[key][BY_RANK[rank].tier] if rank in BY_RANK else 'Bez rangi')
                    else:self.assertEqual(p.faction_membership.faction,'PENDING')
    def test_treasury_and_experience_conserved_across_choices_and_retries(self):
        people=[self.pending('TEMPLAR') for _ in range(3)]
        swamp=CampGuild.objects.get(world=self.c,camp='SWAMP_CAMP');swamp.treasury=101;swamp.experience=59;swamp.level=7;swamp.supply_level=3;swamp.save();self.join()
        for p,key in zip(people,['CITY_WATCH','FIRE_ORDER','WATER_CIRCLE']):
            self.assertTrue(choose(p,key));self.assertTrue(choose(p,key));self.assertFalse(choose(p,'BANDITS'))
            p.refresh_from_db();g=p.faction_membership.guild
            self.assertEqual((g.supply_level,g.level),(3,7))
        self.assertEqual(sum(CampGuild.objects.values_list('treasury',flat=True)),101)
        self.assertEqual(sum(CampGuild.objects.values_list('experience',flat=True)),59)
        swamp.refresh_from_db();self.assertEqual((swamp.treasury,swamp.experience),(0,0))
        self.assertEqual(FactionChoice.objects.count(),3)
    def test_busy_and_active_promotion_preserve_progress_until_player_finishes_or_abandons(self):
        from django.utils import timezone
        from datetime import timedelta
        p=self.pending('NOVICE');self.join()
        quest=CampQuest.objects.create(profile=p,rank_key='GURU',progress={'train:mana':2})
        self.assertFalse(choose(p,'FIRE_ORDER'));quest.refresh_from_db();self.assertEqual(quest.progress,{'train:mana':2})
        self.assertTrue(card(p)['active_quest']);quest.delete()
        p.action_end_time=timezone.now()+timedelta(minutes=1);p.save()
        self.assertFalse(choose(p,'FIRE_ORDER'));self.assertTrue(card(p)['busy'])
    def test_unjoined_nonmember_and_forged_destinations_are_rejected(self):
        p=self.pending('GURU');self.join()
        for key in ['CITY_WATCH','BANDITS','MERCENARIES','PENDING','SWAMP_CAMP','NONE',None,1]:self.assertFalse(choose(p,key))
        World.objects.filter(pk__in=[self.c.pk,self.i.pk]).update(union_key=None)
        self.assertFalse(choose(p,'WATER_CIRCLE'))
    def test_failure_rolls_back_choice_membership_and_both_treasuries(self):
        p=self.pending();self.join();source=p.faction_membership.guild;source.treasury=99;source.save()
        with patch.object(FactionChoice.objects,'create',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):choose(p,'CITY_WATCH')
        p.refresh_from_db();source.refresh_from_db()
        self.assertEqual((p.faction_membership.faction,source.treasury),('PENDING',99));self.assertFalse(FactionChoice.objects.exists())
    def test_chosen_membership_survives_native_promotion_and_mage_branch_has_real_requirements(self):
        from .magic import circle_cap
        p=self.pending('SWAMP_GUARD');p.level=30;p.mana=50;p.ore_balance=1000;p.save();self.join()
        self.assertTrue(choose(p,'FIRE_ORDER'));self.assertEqual(circle_cap(p),4)
        target=BY_RANK['ARCH_GURU']
        with patch('characters.story_gates.missing',return_value=[]):
            self.assertTrue(available_rank(p,target));self.assertFalse(available_rank(p,BY_RANK['TEMPLAR']))
            self.assertFalse(promote_in_camp(p,target.key))
            CampQuest.objects.create(profile=p,rank_key=target.key,progress={g.event:g.count for g in target.objectives})
            self.assertTrue(promote_in_camp(p,target.key));self.assertFalse(promote_in_camp(p,target.key))
        p.refresh_from_db();self.assertEqual(p.faction_membership.faction,'FIRE_ORDER');self.assertEqual(p.guild_name,'Arcymag klasztoru');self.assertEqual(p.ore_balance,650)
        self.assertEqual(FactionChoice.objects.get().original_rank,'SWAMP_GUARD')
    def test_novice_warrior_choice_cannot_later_become_city_guru(self):
        p=self.pending('NOVICE');self.join();self.assertTrue(choose(p,'CITY_WATCH'))
        with patch('characters.story_gates.missing',return_value=[]):
            self.assertTrue(available_rank(p,BY_RANK['SWAMP_GUARD']));self.assertFalse(available_rank(p,BY_RANK['GURU']))
    def test_mage_keeps_native_rune_and_unlocks_destination_without_learning_grants(self):
        from .magic import rune_allowed,BY_KEY,circle_cap
        p=self.pending('ARCH_GURU');p.magic_skill=5;p.save();self.join();self.assertTrue(choose(p,'WATER_CIRCLE'))
        self.assertTrue(rune_allowed(p,BY_KEY['pyrokinesis']));self.assertTrue(rune_allowed(p,BY_KEY['icewave']));self.assertFalse(rune_allowed(p,BY_KEY['firerain']))
        self.assertEqual(circle_cap(p),6);p.refresh_from_db();self.assertEqual(p.magic_skill,5)
    def test_gear_preserves_native_and_unlocks_destination_only(self):
        from .equipment import allowed
        p=self.pending();self.join();self.assertTrue(choose(p,'CITY_WATCH'))
        for camp,expected in [('SWAMP_CAMP',True),('CITY_WATCH',True),('ONAR_MERCS',False)]:
            bp=ItemBluePrint.objects.create(name=camp,required_camp=camp,kind='armor',source_game='adaptation')
            self.assertEqual(allowed(p,bp),expected)
    def test_new_faction_headquarters_unlock_without_losing_native_access(self):
        from .barrier import travel
        from .locations import BY_KEY
        p=self.pending();p.level=30;p.save();self.join();self.assertTrue(choose(p,'FIRE_ORDER'))
        self.assertTrue(BY_KEY['brotherhood_temple'].accessible(p))
        self.assertTrue(travel(p,self.i.pk));self.assertTrue(BY_KEY['k2_monastery'].accessible(p))

    def test_form_is_csrf_protected_and_shows_only_mage_destinations(self):
        p=self.pending('GURU');self.join();self.client.force_login(p.user)
        response=self.client.get(reverse('camp_page'));self.assertEqual(response.status_code,200)
        self.assertEqual([o['key'] for o in response.context['brotherhood']['options']],['FIRE_ORDER','WATER_CIRCLE'])
        guarded=Client(enforce_csrf_checks=True);guarded.force_login(p.user)
        self.assertEqual(guarded.post(reverse('camp_page'),{'action':'choose_faction','faction':'FIRE_ORDER'}).status_code,403)
        self.assertEqual(self.client.post(reverse('camp_page'),{'action':'choose_faction','faction':'FIRE_ORDER'}).status_code,302)
        p.refresh_from_db();self.assertEqual(p.faction_membership.faction,'FIRE_ORDER')
    def test_bot_uses_same_allowlisted_action_and_replay(self):
        from .bots import tick_bot
        from .bot_telemetry import replay_decision
        p=self.pending('ARCH_GURU');p.is_bot=True;p.level=30;p.ore_balance=0;p.save();self.join()
        class ChoicePolicy:
            def choose(self,o):return o.camp_action,o.camp_target_id
        action,result=tick_bot(p,policy=ChoicePolicy(),force_active=True)
        self.assertEqual((action,result),('choose_faction',True));self.assertEqual(FactionChoice.objects.count(),1)
        self.assertIn(FactionChoice.objects.get().destination,{'FIRE_ORDER','WATER_CIRCLE'})
        p.refresh_from_db();self.assertEqual(p.bot_turn,1)


@skipUnlessDBFeature('has_select_for_update')
class ChoiceContentionTests(TransactionTestCase):
    def test_competing_choices_and_different_members_conserve_escrow(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        c,i,race=fixture();people=[person(c,'SWAMP_CAMP','TEMPLAR') for _ in range(2)];succeed(race)
        g=CampGuild.objects.get(world=c,camp='SWAMP_CAMP');g.treasury=999;g.experience=99;g.save();gate=Barrier(3)
        def run(args):
            close_old_connections()
            try:gate.wait(timeout=10);return choose(PlayerProfile.objects.get(pk=args[0]),args[1])
            finally:connections.close_all()
        actions=[(people[0].pk,'CITY_WATCH'),(people[0].pk,'BANDITS'),(people[1].pk,'MERCENARIES')]
        with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,actions))
        for p in people:
            p.refresh_from_db()
            if p.faction_membership.faction=='PENDING':self.assertTrue(choose(p,'MERCENARIES'))
        self.assertEqual(FactionChoice.objects.count(),2)
        self.assertEqual(sum(CampGuild.objects.values_list('treasury',flat=True)),999)
        self.assertEqual(sum(CampGuild.objects.values_list('experience',flat=True)),99)
        g.refresh_from_db();self.assertEqual(g.treasury,0)
