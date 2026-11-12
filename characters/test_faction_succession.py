"""Real domain actions and conserved shared assets across the five-faction split."""
from io import StringIO
from unittest.mock import patch
from uuid import uuid4
from django.apps import apps
from django.contrib.auth.models import User
from django.db import transaction,connections,close_old_connections
from django.test import TestCase,TransactionTestCase,SimpleTestCase,skipUnlessDBFeature
from django.utils import timezone
from .models import (World,CampGuild,PlayerProfile,SleeperRace,FactionMembership,
    FactionSuccession,BarrierEvent,CampContribution,CampQuest,CampRaid,CampRaidStrike)
from .camp_progression import RANKS,BY_RANK
from .faction_succession_v1 import apply,shares,destination
from .barrier import guild_for


def fixture():
    from .worlds import current_world
    c=current_world();c.configured=True;c.bot_count=0;c.save()
    i=World.objects.create(name='Wyspa sukcesji',universe='GOTHIC_II',edition=2,is_open=True,configured=True,bot_count=0)
    for world,camps in [(c,('OLD_CAMP','NEW_CAMP','SWAMP_CAMP')),(i,('CITY_WATCH','FIRE_ORDER','ONAR_MERCS'))]:
        for camp in camps:CampGuild.objects.get_or_create(world=world,camp=camp)
    race=SleeperRace.objects.create(colony=c,khorinis=i,winner=CampGuild.objects.get(world=c,camp='OLD_CAMP'),state='joined',joined_at=timezone.now())
    World.objects.filter(pk__in=[c.pk,i.pk]).update(union_key=uuid4())
    return c,i,race


def person(world,camp,rank,bot=False):
    p=User.objects.create_user('successor-'+uuid4().hex[:12]).playerprofile
    p.world=world;p.camp=camp;p.guild=rank;p.is_bot=bot;p.ore_balance=500;p.save()
    return p


def succeed(race):
    with transaction.atomic():return apply(apps,race)


class AllocationTests(SimpleTestCase):
    def test_every_rounding_conserves_ore_and_is_deterministic(self):
        for total in range(101):
            for counts in ({'BANDITS':2,'FIRE_ORDER':1},{'WATER_CIRCLE':1,'MERCENARIES':2},{}):
                result=shares(total,counts,'BANDITS')
                self.assertEqual(sum(result.values()),total)
                self.assertEqual(result,shares(total,dict(reversed(list(counts.items()))),'BANDITS'))
    def test_exact_eight_rank_catalog_does_not_grant_advanced_promotions(self):
        from .factions import RANK_NAMES,FACTIONS
        self.assertEqual(len(FACTIONS),5)
        for names in RANK_NAMES.values():self.assertEqual(len(names),8)
        self.assertEqual(RANK_NAMES['BANDITS'][:4],('Kopacz','Rzezimieszek','Bandyta','Watażka'))
        self.assertEqual(RANK_NAMES['MERCENARIES'][3],'Kapitan Najemników')
        self.assertFalse(any(r.tier>=4 for r in RANKS))


class SuccessionTests(TestCase):
    def setUp(self):self.c,self.i,self.race=fixture()
    def test_all_native_ranks_map_for_people_and_bots_preserving_entire_personal_rows(self):
        people=[person(self.i if r.camp in {'CITY_WATCH','FIRE_ORDER','ONAR_MERCS'} else self.c,r.camp,r.key,n%2==0) for n,r in enumerate(RANKS)]
        before=list(PlayerProfile.objects.order_by('pk').values());s=succeed(self.race)
        self.assertEqual(before,list(PlayerProfile.objects.order_by('pk').values()))
        self.assertEqual(FactionMembership.objects.count(),len(RANKS))
        for p in people:
            p.refresh_from_db();m=p.faction_membership
            self.assertEqual(m.faction,destination(p.camp,p.guild))
            self.assertEqual((m.historical_camp,m.historical_rank),(p.camp,p.guild))
            self.assertEqual(guild_for(p).pk,m.guild_id)
            if m.faction!='PENDING':
                from .factions import RANK_NAMES
                self.assertEqual(p.guild_name,RANK_NAMES[m.faction][BY_RANK[p.guild].tier])
        self.assertEqual(succeed(self.race).pk,s.pk)
        self.assertEqual(BarrierEvent.objects.filter(kind='factions_succeeded').count(),1)
    def test_member_weighted_split_keeps_ore_experience_upgrades_and_history(self):
        for rank in ('GUARD','BARON','FIRE_MAGE'):person(self.c,'OLD_CAMP',rank)
        old=CampGuild.objects.get(world=self.c,camp='OLD_CAMP');old.treasury=101;old.experience=91;old.level=8;old.training_level=3;old.save()
        totals=lambda:(sum(CampGuild.objects.values_list('treasury',flat=True)),sum(CampGuild.objects.values_list('experience',flat=True)))
        before=totals();s=succeed(self.race)
        bandits=CampGuild.objects.get(world=self.c,camp='BANDITS');fire=CampGuild.objects.get(world=self.i,camp='FIRE_ORDER')
        self.assertEqual((bandits.treasury,fire.treasury),(67,34));self.assertEqual(totals(),before)
        self.assertEqual((bandits.training_level,fire.training_level),(3,3));self.assertEqual(bandits.level,8)
        from .camp_guilds import credit_guild
        credit_guild(bandits,1,0);self.assertEqual(bandits.level,8)
        self.assertEqual(s.details['policy'],'member_count_largest_remainder')
        self.assertEqual(succeed(self.race).details,s.details)
    def test_old_lee_onar_pool_uses_both_populations_and_never_double_transfers(self):
        water=person(self.c,'NEW_CAMP','ARCH_WATER');merc=person(self.c,'NEW_CAMP','MERC');onar=person(self.i,'ONAR_MERCS','K2_CAPTAIN')
        lee=CampGuild.objects.get(world=self.c,camp='NEW_CAMP');lee.treasury=300;lee.experience=300;lee.save()
        historical=CampGuild.objects.get(world=self.i,camp='ONAR_MERCS');historical.experience=100;historical.save()
        BarrierEvent.objects.create(race=self.race,kind='mercenaries_united',details={})
        succeed(self.race)
        self.assertEqual(guild_for(water).treasury,100);self.assertEqual(guild_for(merc).treasury,200);self.assertEqual(guild_for(merc).pk,guild_for(onar).pk)
        self.assertEqual((guild_for(water).experience,guild_for(merc).experience),(100,200))
    def test_empty_source_has_deterministic_successor_and_brotherhood_is_escrow(self):
        old=CampGuild.objects.get(world=self.c,camp='OLD_CAMP');old.treasury=123;old.save()
        p=person(self.c,'SWAMP_CAMP','GURU');swamp=guild_for(p);swamp.treasury=77;swamp.save()
        succeed(self.race);p.refresh_from_db()
        self.assertEqual(p.faction_membership.faction,'PENDING');self.assertEqual(guild_for(p).treasury,77)
        self.assertEqual(CampGuild.objects.get(world=self.c,camp='BANDITS').treasury,123)
        from .game_logic import start_mining
        self.assertTrue(start_mining(p,15))
    def test_retry_donation_and_new_guild_actions_are_not_misrouted(self):
        from .camp_guilds import donate_to_camp,record_guild_event,guild_cards
        p=person(self.c,'NEW_CAMP','WATER_MAGE');key=uuid4()
        self.assertTrue(donate_to_camp(p,10,key));succeed(self.race);p.refresh_from_db()
        self.assertTrue(donate_to_camp(p,10,key));self.assertTrue(donate_to_camp(p,20,uuid4()))
        with transaction.atomic():record_guild_event(p,'mine')
        self.assertEqual(guild_for(p).camp,'WATER_CIRCLE');self.assertEqual(guild_cards(p)['members'],1)
        self.assertEqual(CampContribution.objects.filter(profile=p,kind='donation').count(),2)
        p.refresh_from_db();self.assertEqual(p.ore_balance,470)
    def test_old_raid_rewards_survive_but_new_historical_raids_cannot_be_attacked(self):
        from .camp_raids import claim_camp_raid,strike_camp_raid,rally_camp_raid
        p=person(self.c,'OLD_CAMP','GUARD');p.level=10;p.save();old=guild_for(p)
        raid=CampRaid.objects.create(guild=old,day=timezone.localdate(),name='Stara wyprawa',art_key='crawler_queen',health=0,maximum_health=100,attack=1,protection=0,completed_at=timezone.now())
        hit=CampRaidStrike.objects.create(raid=raid,profile=p,request_key=uuid4(),damage=100,health_cost=1)
        succeed(self.race);p.refresh_from_db()
        self.assertTrue(claim_camp_raid(p,raid.pk));self.assertTrue(claim_camp_raid(p,raid.pk))
        self.assertEqual(strike_camp_raid(p,raid.pk,hit.request_key).pk,hit.pk)
        raid.completed_at=None;raid.health=100;raid.save()
        self.assertFalse(strike_camp_raid(p,raid.pk,uuid4()))
        self.assertEqual(rally_camp_raid(p).guild_id,guild_for(p).pk)
    def test_rollback_is_all_or_nothing(self):
        p=person(self.c,'OLD_CAMP','GUARD');old=guild_for(p);old.treasury=333;old.save()
        with patch('django.db.models.query.QuerySet.bulk_create',side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):succeed(self.race)
        old.refresh_from_db();self.assertEqual(old.treasury,333)
        self.assertFalse(FactionSuccession.objects.exists());self.assertFalse(CampGuild.objects.filter(camp='BANDITS').exists())
    def test_rank_completion_enrolls_new_joined_characters_and_preserves_snapshot(self):
        from .factions import enroll
        from .game_logic import choose_camp
        succeed(self.race);p=person(self.c,'NONE','NONE')
        with patch('characters.story_gates.missing',return_value=[]):
            self.assertFalse(choose_camp(p,'SWAMP_CAMP'));self.assertTrue(choose_camp(p,'OLD_CAMP'))
        p.refresh_from_db();self.assertEqual(p.faction_membership.faction,'BANDITS')
        p.guild='FIRE_MAGE';p.save()
        with transaction.atomic():enroll(p)
        self.assertEqual(p.faction_membership.faction,'FIRE_ORDER');self.assertEqual(p.faction_membership.historical_rank,'NONE')
    def test_real_promotion_moves_native_mage_branch_and_keeps_history_and_magic(self):
        from .camp_progression import promote_in_camp
        from .magic import circle_cap
        p=person(self.c,'OLD_CAMP','SHADOW',bot=True);p.level=10;p.mana=30;p.save()
        succeed(self.race);p.refresh_from_db()
        rank=BY_RANK['FIRE_MAGE']
        CampQuest.objects.create(profile=p,rank_key=rank.key,progress={g.event:g.count for g in rank.objectives})
        with patch('characters.story_gates.missing',return_value=[]):
            self.assertTrue(promote_in_camp(p,rank.key));self.assertFalse(promote_in_camp(p,rank.key))
        p.refresh_from_db()
        self.assertEqual((p.guild,p.ore_balance),('FIRE_MAGE',400))
        self.assertEqual((p.faction_membership.faction,p.faction_membership.historical_rank),('FIRE_ORDER','SHADOW'))
        self.assertGreaterEqual(circle_cap(p),4)

    def test_ui_shows_five_factions_and_rank_filters_do_not_mix_water_with_mercenaries(self):
        p=person(self.c,'NEW_CAMP','WATER_MAGE');person(self.i,'ONAR_MERCS','K2_CAPTAIN');succeed(self.race)
        self.client.force_login(p.user)
        for route in ('/oboz/','/wspolnota/','/rankingi/'):
            response=self.client.get(route);self.assertEqual(response.status_code,200,route)
        response=self.client.get('/rankingi/?camp=WATER_CIRCLE')
        self.assertContains(response,'Krąg Magów Wody');self.assertEqual(response.context['page'].paginator.count,1)
        self.assertEqual(len(response.context['camps']),5)


class ExistingSaveTests(TransactionTestCase):
    def test_joined_save_requires_successful_backup_and_is_restartable(self):
        from .barrier_activation import activate
        c,i,race=fixture();p=person(c,'OLD_CAMP','GUARD')
        with patch('characters.barrier_activation.fresh_snapshot',side_effect=RuntimeError):self.assertFalse(activate(race.pk))
        self.assertFalse(FactionMembership.objects.exists())
        self.assertFalse(activate(race.pk))  # The retry delay prevents a backup loop.
        SleeperRace.objects.filter(pk=race.pk).update(lease_expires_at=None)
        with patch('characters.barrier_activation.fresh_snapshot',return_value=('/isolated/backup','a'*64,{})) as backup:
            self.assertTrue(activate(race.pk));self.assertTrue(activate(race.pk));self.assertEqual(backup.call_count,1)
        self.assertEqual(FactionMembership.objects.get(profile=p).faction,'BANDITS')
        self.assertEqual(FactionSuccession.objects.get().details['backup']['digest'],'a'*64)


@skipUnlessDBFeature('has_select_for_update')
class SuccessionContentionTests(TransactionTestCase):
    def test_competing_succession_transfers_assets_once(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        c,i,race=fixture();person(c,'OLD_CAMP','GUARD');g=CampGuild.objects.get(world=c,camp='OLD_CAMP');g.treasury=999;g.save();gate=Barrier(2)
        def run(n):
            close_old_connections()
            try:
                gate.wait(timeout=10)
                with transaction.atomic():
                    locked=SleeperRace.objects.select_for_update().get(pk=race.pk)
                    return apply(apps,locked).pk
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:result=list(pool.map(run,range(2)))
        self.assertEqual(result[0],result[1]);self.assertEqual(sum(CampGuild.objects.values_list('treasury',flat=True)),999)
        self.assertEqual(FactionMembership.objects.count(),1)
