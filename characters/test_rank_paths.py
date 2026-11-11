"""Four-rank catalog and compatibility with already earned water promotions."""
from importlib import import_module
from unittest.mock import patch
from django.apps import apps
from django.contrib.auth.models import User
from django.db import connection
from django.test import SimpleTestCase,TestCase,TransactionTestCase
from django.urls import reverse
from .camp_progression import (RANKS,BY_RANK,CAMP_PATHS,RANK_RULES_VERSION,rank_mapping,
    available_rank,accept_camp_quest,promote_in_camp,rank_cards,record_camp_event)
from .models import PlayerProfile,CampQuest
from .camp_privileges import privileges

class RankPathCatalogTests(SimpleTestCase):
    def test_every_basic_branch_has_four_ordered_ranks(self):
        self.assertEqual(RANK_RULES_VERSION,2)
        for camp,paths in CAMP_PATHS.items():
            for path in paths:
                self.assertEqual(len(path),4)
                ranks=[next(r for r in RANKS if r.camp==camp and r.name==name) for name in path]
                self.assertEqual([r.tier for r in ranks],[0,1,2,3])
                for parent,child in zip(ranks,ranks[1:]):self.assertIn(parent.key,child.parents)
        self.assertFalse(any('paladyn' in r.name.lower() for r in RANKS))
    def test_mapping_covers_every_legacy_identity_without_changing_cost_or_objectives(self):
        from .camp_progression import LEGACY_RANKS
        mapping=rank_mapping();self.assertEqual(set(mapping),set(BY_RANK))
        for key,rank in BY_RANK.items():
            old=LEGACY_RANKS[key]
            self.assertEqual((rank.key,rank.cost,rank.level,rank.objectives),(old.key,old.cost,old.level,old.objectives))
            self.assertEqual(mapping[key]['from_version'],1)
            self.assertEqual(mapping[key]['to_version'],2)
        self.assertEqual(mapping['K2_PALADIN']['old_name'],'Paladyn')
        self.assertEqual(mapping['K2_PALADIN']['name'],'Sierżant straży')

class RankPathTests(TestCase):
    def setUp(self):
        from .world_management import seed_clean_world
        seed_clean_world();self.p=User.objects.create_user('rank-path').playerprofile
        self.p.camp='NEW_CAMP';self.p.guild='ROGUE';self.p.level=30;self.p.mana=100;self.p.ore_balance=1000;self.p.save()
        from .testing_story import promotion_prerequisites
        promotion_prerequisites(self.p)
    def finish(self,key):
        rank=BY_RANK[key]
        CampQuest.objects.filter(profile=self.p,rank_key=key).update(progress={g.event:g.count for g in rank.objectives})
        before=self.p.ore_balance
        self.assertTrue(promote_in_camp(self.p,key));self.p.refresh_from_db()
        self.assertEqual(self.p.ore_balance,before-rank.cost)
        self.assertFalse(promote_in_camp(self.p,key))
    def test_new_water_path_forks_from_rogue_and_preserves_branch_exclusivity(self):
        self.assertTrue(accept_camp_quest(self.p,'WATER_MAGE'));self.finish('WATER_MAGE')
        self.assertEqual(self.p.camp_tier,2)
        self.assertFalse(accept_camp_quest(self.p,'MERC'))
        self.assertTrue(accept_camp_quest(self.p,'ARCH_WATER'));self.finish('ARCH_WATER')
        self.assertEqual(self.p.camp_tier,3)
    def test_new_warrior_cannot_switch_to_water_after_choosing_mercenary(self):
        self.p.guild='MERC';self.p.save()
        self.assertFalse(accept_camp_quest(self.p,'WATER_MAGE'))
        self.assertTrue(accept_camp_quest(self.p,'ELITE_MERC'))
    def test_pending_legacy_water_promotion_and_benefits_survive(self):
        self.p.guild='MERC';self.p.legacy_water_path=True;self.p.save()
        self.assertTrue(accept_camp_quest(self.p,'WATER_MAGE'))
        record_camp_event(self.p,'train:mana')
        self.assertEqual(CampQuest.objects.get(profile=self.p).progress,{'train:mana':1})
        self.finish('WATER_MAGE');self.assertEqual(self.p.camp_tier,3)
        self.assertEqual(privileges(self.p)['supply'],3)
        self.assertTrue(accept_camp_quest(self.p,'ARCH_WATER'));self.finish('ARCH_WATER')
        self.assertEqual(self.p.camp_tier,4);self.assertEqual(privileges(self.p)['defense'],2)
    def test_legacy_story_gates_remain_and_cards_show_effective_requirements(self):
        self.p.guild='MERC';self.p.legacy_water_path=True;self.p.save()
        with patch('characters.story_gates.missing',return_value=[{'key':'free-depths','title':'Próba'}]) as missing:
            self.assertFalse(available_rank(self.p,BY_RANK['WATER_MAGE']))
            self.assertEqual(missing.call_args.args[1],3)
        card=next(c for c in rank_cards(self.p) if c['rank'].key=='WATER_MAGE')
        self.assertEqual(card['parents'],'Najemnik');self.assertEqual(card['ordinal'],3)
    def test_new_path_works_for_bot_and_cannot_inject_legacy_flag(self):
        self.p.is_bot=True;self.p.save()
        self.assertTrue(accept_camp_quest(self.p,'WATER_MAGE'));self.finish('WATER_MAGE')
        self.p.is_bot=False;self.p.save();self.client.force_login(self.p.user)
        self.client.post(reverse('camp_page'),{'action':'accept','rank':'ARCH_WATER','legacy_water_path':'true'})
        self.p.refresh_from_db();self.assertFalse(self.p.legacy_water_path)
    def test_compatibility_data_step_preserves_every_existing_column_and_is_idempotent(self):
        pending=User.objects.create_user('pending-water').playerprofile
        pending.camp='NEW_CAMP';pending.guild='ROGUE';pending.save()
        CampQuest.objects.create(profile=pending,rank_key='MERC',progress={'train:strength':1})
        self.p.guild='ARCH_WATER';self.p.save()
        outsider=User.objects.create_user('foreign-rank').playerprofile
        outsider.camp='OLD_CAMP';outsider.guild='MERC';outsider.save()
        profile_rows=list(PlayerProfile.objects.order_by('pk').values());quests=list(CampQuest.objects.values())
        migrate=import_module('characters.migrations.0048_rowne_podstawowe_rangi').preserve_water_path
        from types import SimpleNamespace
        editor=SimpleNamespace(connection=connection)
        migrate(apps,editor);migrate(apps,editor)
        after=list(PlayerProfile.objects.order_by('pk').values())
        for old,new in zip(profile_rows,after):
            self.assertEqual({k:v for k,v in old.items() if k!='legacy_water_path'},
                             {k:v for k,v in new.items() if k!='legacy_water_path'})
        self.assertEqual(list(CampQuest.objects.values()),quests)
        for p,expected in ((self.p,True),(pending,True),(outsider,False)):
            p.refresh_from_db();self.assertEqual(p.legacy_water_path,expected)
        fresh=User.objects.create_user('fresh-after-migration').playerprofile
        self.assertFalse(fresh.legacy_water_path)

from django.db.migrations.executor import MigrationExecutor

class RankSchemaMigrationTests(TransactionTestCase):
    def test_real_0047_save_upgrades_without_rewriting_existing_fields(self):
        executor=MigrationExecutor(connection);latest=executor.loader.graph.leaf_nodes('characters')
        old_target=[('characters','0047_wspolna_hierarchia_najemnikow')]
        try:
            executor.migrate(old_target);old=executor.loader.project_state(old_target).apps
            Profile=old.get_model('characters','PlayerProfile');Quest=old.get_model('characters','CampQuest')
            Account=old.get_model('auth','User');World=old.get_model('characters','World')
            world=World.objects.filter(is_current=True).first() or World.objects.create(name='Migration fixture',is_current=True)
            ids=[]
            for index,rank in enumerate(('MERC','WATER_MAGE','ARCH_WATER','ROGUE','ROGUE')):
                user=Account.objects.create(username='old-rank-'+str(index))
                p=Profile.objects.create(user_id=user.pk,world_id=world.pk,camp='NEW_CAMP',guild=rank,level=25,ore_balance=987,mana=55)
                ids.append(p.pk)
            Quest.objects.create(profile_id=ids[3],rank_key='MERC',progress={'train:strength':1})
            before=list(Profile.objects.filter(pk__in=ids).order_by('pk').values());quests=list(Quest.objects.values())
            executor=MigrationExecutor(connection);executor.migrate(latest)
            new=executor.loader.project_state(latest).apps
            rows=list(new.get_model('characters','PlayerProfile').objects.filter(pk__in=ids).order_by('pk').values())
            self.assertEqual([row['legacy_water_path'] for row in rows],[True,True,True,True,False])
            self.assertEqual([{key:row[key] for key in before[0]} for row in rows],before)
            self.assertEqual(list(new.get_model('characters','CampQuest').objects.values()),quests)
        finally:MigrationExecutor(connection).migrate(latest)
