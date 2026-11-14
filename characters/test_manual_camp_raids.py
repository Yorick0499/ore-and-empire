"""Human orders accelerate an earned guild, not bot cadence or free progression."""
from datetime import datetime,timedelta
from unittest import skipUnless
from unittest.mock import patch
from uuid import uuid4
from django.contrib.auth.models import User
from django.db import connection,transaction,IntegrityError
from django.test import TestCase,TransactionTestCase
from django.utils import timezone
from .models import PlayerProfile,World,CampGuild,CampRaid,CampRaidStrike,CampRaidReward
from .camp_raids import (rally_manual_raid,can_rally_manual,raid_card,
                         rally_camp_raid,strike_camp_raid,claim_camp_raid)
from .world_clock import POLISH_TIME


def captain(name='captain',camp='OLD_CAMP',rank='BARON'):
    p=User.objects.create_user(name).playerprofile
    p.camp=camp;p.guild=rank;p.level=35;p.strength=400;p.life=1000;p.current_health=1000
    p.world.configured=True;p.world.bot_count=0;p.world.save()
    p.save()
    CampGuild.objects.get_or_create(world=p.world,camp=camp)
    return p


class ManualRaidTests(TestCase):
    def setUp(self):self.p=captain()

    def finish(self,raid):
        strike=strike_camp_raid(self.p,raid.pk,uuid4())
        self.assertTrue(strike);raid.refresh_from_db();self.assertEqual(raid.health,0)
        return strike

    def test_all_six_highest_colony_ranks_can_order_but_lower_and_legacy_mages_cannot(self):
        for n,(camp,rank) in enumerate([('OLD_CAMP','BARON'),('OLD_CAMP','ARCH_FIRE'),('NEW_CAMP','ELITE_MERC'),('NEW_CAMP','ARCH_WATER'),('SWAMP_CAMP','TEMPLAR'),('SWAMP_CAMP','ARCH_GURU')]):
            with self.subTest(rank=rank):self.assertTrue(can_rally_manual(captain('rank'+str(n),camp,rank)))
        self.p.camp='NEW_CAMP';self.p.guild='WATER_MAGE';self.p.legacy_water_path=True;self.p.save()
        self.assertEqual(self.p.camp_tier,3)
        self.assertFalse(rally_manual_raid(self.p,uuid4()))
        self.assertFalse(CampRaid.objects.exists())

    def test_order_is_human_only_and_not_available_in_khorinis_or_after_union(self):
        self.p.is_bot=True;self.p.save();self.assertFalse(rally_manual_raid(self.p,uuid4()))
        self.p.is_bot=False;self.p.save()
        island=World.objects.create(name='Island',universe='GOTHIC_II',is_open=True,configured=True,bot_count=0)
        visitor=captain('islander','CITY_WATCH','K2_COMMANDER');visitor.world=island;visitor.save()
        self.assertFalse(rally_manual_raid(visitor,uuid4()))
        key=uuid4();World.objects.filter(pk__in=[self.p.world_id,island.pk]).update(union_key=key)
        self.assertFalse(rally_manual_raid(self.p,uuid4()))
        self.assertFalse(CampRaid.objects.exists())

    def test_repeat_requests_do_not_respawn_finished_targets_and_new_orders_work_same_day(self):
        key=uuid4();first=rally_manual_raid(self.p,key)
        self.assertEqual(rally_manual_raid(self.p,key).pk,first.pk)
        self.assertFalse(rally_manual_raid(self.p,uuid4()))
        guild=CampGuild.objects.get(world=self.p.world,camp=self.p.camp)
        self.assertEqual((guild.experience,guild.treasury),(0,0))
        self.finish(first)
        self.assertEqual(rally_manual_raid(self.p,key).pk,first.pk)
        second=rally_manual_raid(self.p,uuid4())
        self.assertNotEqual(first.pk,second.pk);self.assertEqual(first.day,second.day)
        guild.refresh_from_db();self.assertEqual((guild.experience,guild.treasury),(60,100))
        self.assertEqual(CampRaid.objects.filter(cycle='manual').count(),2)

    def test_invalid_requests_other_camps_and_unauthorized_http_cannot_create_orders(self):
        for key in (None,'', 'not-a-uuid'):self.assertFalse(rally_manual_raid(self.p,key))
        other=captain('other','NEW_CAMP','ARCH_WATER')
        raid=rally_manual_raid(self.p,uuid4())
        self.assertFalse(strike_camp_raid(other,raid.pk,uuid4()))
        self.p.guild='GUARD';self.p.save();self.client.force_login(self.p.user)
        self.client.post('/wspolnota/',{'action':'manual_rally','request_key':uuid4()})
        self.assertEqual(CampRaid.objects.count(),1)
        self.assertEqual(CampRaidStrike.objects.count(),0)

    def test_normal_costs_rewards_retry_and_rollback_apply_to_manual_targets(self):
        raid=rally_manual_raid(self.p,uuid4());key=uuid4()
        with patch.object(CampRaidStrike.objects,'create',side_effect=RuntimeError('write failed')):
            with self.assertRaises(RuntimeError):strike_camp_raid(self.p,raid.pk,key)
        raid.refresh_from_db();self.p.refresh_from_db()
        self.assertEqual(raid.health,raid.maximum_health);self.assertEqual(self.p.current_energy,100)
        guild=raid.guild;guild.refresh_from_db();self.assertEqual(guild.experience,0)
        strike=self.finish(raid)
        self.p.refresh_from_db();self.assertEqual(self.p.current_energy,80)
        self.assertEqual(strike_camp_raid(self.p,raid.pk,strike.request_key).pk,strike.pk)
        self.assertTrue(claim_camp_raid(self.p,raid.pk));self.assertTrue(claim_camp_raid(self.p,raid.pk))
        self.p.refresh_from_db();self.assertEqual((self.p.ore_balance,self.p.premium_balance),(60,1))
        self.assertEqual(CampRaidReward.objects.filter(raid=raid).count(),1)

    def test_daily_target_stays_unique_and_bot_can_join_a_human_order(self):
        daily=rally_camp_raid(self.p)
        order=rally_manual_raid(self.p,uuid4())
        self.assertEqual(rally_camp_raid(self.p).pk,daily.pk)
        helper=captain('bot');helper.guild='SHADOW';helper.is_bot=True;helper.level=10
        helper.strength=50;helper.life=200;helper.current_health=200;helper.bot_turn=13;helper.save()
        self.assertEqual(raid_card(helper,include_manual=True)['raid'].pk,daily.pk)
        self.finish(daily)
        self.assertEqual(raid_card(helper,include_manual=True)['raid'].pk,order.pk)
        from .bots import tick_bot
        self.assertEqual(tick_bot(helper,force_active=True),('raid_strike',True))
        self.assertTrue(CampRaidStrike.objects.filter(raid=order,profile=helper).exists())
        self.assertFalse(rally_manual_raid(helper,uuid4()))

    def test_midnight_preserves_manual_progress_but_new_day_daily_is_independent(self):
        now=datetime(2026,11,14,23,59,tzinfo=POLISH_TIME)
        with patch('django.utils.timezone.now',return_value=now):
            order=rally_manual_raid(self.p,uuid4());daily=rally_camp_raid(self.p)
        with patch('django.utils.timezone.now',return_value=now+timedelta(minutes=2)):
            self.assertEqual(raid_card(self.p,'manual')['raid'].pk,order.pk)
            self.assertIsNone(raid_card(self.p,'manual')['ends_at'])
            self.assertTrue(strike_camp_raid(self.p,order.pk,uuid4()))
            self.assertNotEqual(rally_camp_raid(self.p).pk,daily.pk)

    def test_level_ten_stops_new_orders_and_union_stops_unfinished_manual_strikes(self):
        raid=rally_manual_raid(self.p,uuid4())
        CampGuild.objects.filter(pk=raid.guild_id).update(level=10,experience=900)
        self.assertFalse(can_rally_manual(self.p))
        self.assertFalse(rally_manual_raid(self.p,uuid4()))
        # An already open target may finish before the global transition.
        self.finish(raid);self.assertTrue(claim_camp_raid(self.p,raid.pk))
        CampGuild.objects.filter(pk=raid.guild_id).update(level=9,experience=800)
        opened=rally_manual_raid(self.p,uuid4())
        island=World.objects.create(universe='GOTHIC_II',is_open=True,configured=True,bot_count=0)
        World.objects.filter(pk__in=[self.p.world_id,island.pk]).update(union_key=uuid4())
        self.assertFalse(strike_camp_raid(self.p,opened.pk,uuid4()))
        self.assertIsNone(raid_card(self.p,'manual')['raid'])

    def test_database_guards_active_order_and_daily_uniqueness(self):
        raid=rally_manual_raid(self.p,uuid4())
        for cycle in ('manual','daily'):
            original=raid if cycle=='manual' else rally_camp_raid(self.p)
            original.pk=None;original.rally_request=uuid4() if cycle=='manual' else None
            with transaction.atomic(),self.assertRaises(IntegrityError):original.save(force_insert=True)

    def test_join_committed_while_waiting_for_guild_lock_cannot_create_an_order(self):
        from .barrier import guild_for
        island=World.objects.create(universe='GOTHIC_II',is_open=True,configured=True,bot_count=0)
        def join_before_lock(profile,lock=False):
            guild=guild_for(profile,lock=lock)
            World.objects.filter(pk__in=[profile.world_id,island.pk]).update(union_key=uuid4())
            return guild
        with patch('characters.camp_raids.guild_for',side_effect=join_before_lock):
            self.assertFalse(rally_manual_raid(self.p,uuid4()))
        self.assertFalse(CampRaid.objects.exists())

    def test_panel_has_actionable_post_and_no_raid_created_by_get(self):
        self.client.force_login(self.p.user)
        response=self.client.get('/wspolnota/')
        self.assertContains(response,'Ogłoś dodatkową wyprawę na rozkaz')
        self.assertFalse(CampRaid.objects.exists())
        html=response.content.decode();title=html.split('<title>')[1].split('</title>')[0]
        self.assertNotIn('<section',title)
        self.client.post('/wspolnota/',{'action':'manual_rally','request_key':uuid4()})
        response=self.client.get('/wspolnota/')
        self.assertContains(response,'Wyrusz na rozkaz (20 energii)')
        self.assertNotContains(response,'Ogłoś dodatkową wyprawę na rozkaz')
        self.assertEqual(CampRaid.objects.filter(cycle='manual').count(),1)

    def test_backup_proof_protects_manual_author_and_idempotency_key(self):
        import sqlite3
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from .backups import inspect_database
        with TemporaryDirectory() as folder:
            path=Path(folder)/'proof.sqlite3'
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE characters_campraid (id INTEGER PRIMARY KEY, cycle TEXT, rallied_by_id INTEGER, rally_request TEXT)')
                db.execute('INSERT INTO characters_campraid VALUES (1,?,?,?)',('manual',1,str(uuid4())))
            before=inspect_database(path)['characters_campraid']
            self.assertIn('rally_request',before['columns']);self.assertIn('rallied_by_id',before['columns'])
            with sqlite3.connect(path) as db:db.execute('UPDATE characters_campraid SET rallied_by_id=2')
            changed=inspect_database(path)['characters_campraid']
            self.assertNotEqual(changed['digest'],before['digest'])
            with sqlite3.connect(path) as db:db.execute('UPDATE characters_campraid SET rally_request=?',(str(uuid4()),))
            self.assertNotEqual(inspect_database(path)['characters_campraid']['digest'],changed['digest'])


@skipUnless(connection.vendor=='postgresql','Requires genuine PostgreSQL row locks')
class ManualRaidConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.a=captain('a');self.b=captain('b')
    def race(self,callback):
        from . import test_concurrency
        return test_concurrency.PostgreSQLConcurrencyTests.race(self,callback)
    def test_same_request_creates_one_target(self):
        key=uuid4()
        ids=self.race(lambda n:rally_manual_raid(PlayerProfile.objects.get(pk=self.a.pk),key).pk)
        self.assertEqual(ids[0],ids[1]);self.assertEqual(CampRaid.objects.count(),1)
    def test_two_human_commanders_cannot_create_parallel_targets(self):
        def order(n):
            result=rally_manual_raid(PlayerProfile.objects.get(pk=[self.a.pk,self.b.pk][n]),uuid4())
            return bool(result)
        self.assertEqual(sorted(self.race(order)),[False,True])
        self.assertEqual(CampRaid.objects.filter(completed_at__isnull=True).count(),1)
    def test_final_blow_and_new_order_cannot_bypass_level_ten(self):
        raid=rally_manual_raid(self.a,uuid4());raid.health=1;raid.save(update_fields=['health'])
        CampGuild.objects.filter(pk=raid.guild_id).update(level=9,experience=850)
        def action(n):
            p=PlayerProfile.objects.get(pk=[self.a.pk,self.b.pk][n])
            return bool(strike_camp_raid(p,raid.pk,uuid4()) if n==0 else rally_manual_raid(p,uuid4()))
        self.assertEqual(self.race(action),[True,False])
        raid.guild.refresh_from_db();self.assertEqual(raid.guild.level,10)
        self.assertEqual(CampRaid.objects.count(),1);self.assertEqual(CampRaidStrike.objects.count(),1)


class RaidProgressClarityTests(TestCase):
    def setUp(self):self.p=captain('clarity','NEW_CAMP','ARCH_WATER')

    def test_same_target_never_resets_and_new_target_has_distinct_number_and_progress(self):
        guild=CampGuild.objects.get(world=self.p.world,camp='NEW_CAMP')
        guild.level=4;guild.experience=360;guild.save()
        key=uuid4();raid=rally_manual_raid(self.p,key)
        raid.health=258;raid.save(update_fields=['health'])
        self.client.force_login(self.p.user)
        before=(raid.name,raid.art_key,raid.maximum_health,raid.health)
        response=self.client.get('/wspolnota/')
        self.assertContains(response,'Do poziomu 5 brakuje 40 PD.')
        self.assertContains(response,'faza walki 2/3 tego przeciwnika')
        self.assertContains(response,'Wyprawa na rozkaz #1')
        self.assertEqual(rally_manual_raid(self.p,key).pk,raid.pk)
        raid.refresh_from_db();self.assertEqual((raid.name,raid.art_key,raid.maximum_health,raid.health),before)
        self.assertTrue(strike_camp_raid(self.p,raid.pk,uuid4()))
        second=rally_manual_raid(self.p,uuid4());self.assertNotEqual(second.art_key,raid.art_key)
        response=self.client.get('/wspolnota/')
        self.assertContains(response,'Wyprawa na rozkaz #1 ukończona.')
        self.assertContains(response,'Wyprawa na rozkaz #2')
        self.assertContains(response,'faza walki 1/3 tego przeciwnika')
        self.assertContains(response,'Do poziomu 6 brakuje 80 PD.')
        guild.refresh_from_db();self.assertEqual((guild.level,guild.experience),(5,420))

    def test_new_orders_rotate_in_all_colony_camps_without_changing_encounter_balance(self):
        from .camp_raids import COLONY_ENCOUNTERS
        import json
        from .gothic_assets import MANIFEST_PATH
        available=json.loads(MANIFEST_PATH.read_bytes())
        self.assertTrue(all(art in available for pool in COLONY_ENCOUNTERS.values() for _,art in pool))
        for n,(camp,rank) in enumerate([('OLD_CAMP','BARON'),('NEW_CAMP','ARCH_WATER'),('SWAMP_CAMP','ARCH_GURU')]):
            p=captain('rotation'+str(n),camp,rank);arts=[]
            for _ in range(5):
                guild=CampGuild.objects.get(world=p.world,camp=camp)
                raid=rally_manual_raid(p,uuid4());self.assertTrue(raid)
                self.assertEqual((raid.maximum_health,raid.attack,raid.protection),(500+100*guild.level,10+2*guild.level,4+2*guild.level))
                arts.append(raid.art_key)
                self.assertTrue(strike_camp_raid(p,raid.pk,uuid4()))
                raid.refresh_from_db();self.assertEqual(raid.health,0)
            self.assertEqual(len(set(arts[:4])),4)
            self.assertTrue(all(a!=b for a,b in zip(arts,arts[1:])))
            self.assertEqual(arts[0],arts[4])
            self.assertEqual(set(arts),{row[1] for row in COLONY_ENCOUNTERS[camp]})

    def test_daily_snapshot_survives_rotation_and_bot_cards_do_not_request_ui_counts(self):
        daily=rally_camp_raid(self.p);before=(daily.name,daily.art_key,daily.health)
        manual=rally_manual_raid(self.p,uuid4())
        self.assertNotEqual(daily.art_key,manual.art_key)
        self.assertEqual(rally_camp_raid(self.p).pk,daily.pk)
        daily.refresh_from_db();self.assertEqual((daily.name,daily.art_key,daily.health),before)
        card=raid_card(self.p,include_manual=True)
        self.assertNotIn('number',card);self.assertNotIn('latest_completed',card)

    def test_completed_daily_does_not_show_a_phase_as_if_it_were_ongoing(self):
        raid=rally_camp_raid(self.p)
        self.assertTrue(strike_camp_raid(self.p,raid.pk,uuid4()))
        self.client.force_login(self.p.user)
        response=self.client.get('/wspolnota/')
        self.assertContains(response,'Wyprawa dzienna #1')
        self.assertContains(response,'cel pokonany')
        self.assertNotContains(response,'faza walki 3/3 tego przeciwnika')


class ManualRaidMigrationTests(TransactionTestCase):
    def test_forward_upgrade_keeps_daily_weekly_history_and_resources(self):
        from django.db.migrations.executor import MigrationExecutor
        previous=('characters','0054_world_updates_events');latest=('characters','0055_manual_camp_raids')
        def migrate(target):
            executor=MigrationExecutor(connection);executor.migrate([target])
            return executor.loader.project_state([target]).apps
        self.addCleanup(migrate,latest)
        apps=migrate(previous)
        UserOld=apps.get_model('auth','User');WorldOld=apps.get_model('characters','World')
        Profile=apps.get_model('characters','PlayerProfile');Guild=apps.get_model('characters','CampGuild')
        Raid=apps.get_model('characters','CampRaid');Strike=apps.get_model('characters','CampRaidStrike');Reward=apps.get_model('characters','CampRaidReward')
        world=WorldOld.objects.first() or WorldOld.objects.create(name='Preserved')
        user=UserOld.objects.create(username='preserved');p=Profile.objects.create(user_id=user.pk,world_id=world.pk,ore_balance=777,premium_balance=9)
        guild,_=Guild.objects.get_or_create(world_id=world.pk,camp='NEW_CAMP')
        raids=[Raid.objects.create(guild_id=guild.pk,cycle=cycle,day=timezone.now().date(),name=cycle,art_key='orc_warrior',maximum_health=600,health=0,attack=12,protection=6,completed_at=timezone.now()) for cycle in ('daily','weekly')]
        strike=Strike.objects.create(raid_id=raids[0].pk,profile_id=p.pk,request_key=uuid4(),damage=600,health_cost=10,log=['preserved'])
        reward=Reward.objects.create(raid_id=raids[0].pk,profile_id=p.pk)
        snapshots={model._meta.model_name:list(model.objects.order_by('pk').values()) for model in (Profile,Guild,Raid,Strike,Reward)}
        apps=migrate(latest)
        for name,rows in snapshots.items():
            after=list(apps.get_model('characters',name).objects.order_by('pk').values(*rows[0].keys())) if rows else []
            self.assertEqual(after,rows,name)
        self.assertFalse(CampRaid.objects.exclude(rallied_by=None,rally_request=None).exists())
