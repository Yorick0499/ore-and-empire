import json,os,sqlite3,subprocess,sys
from pathlib import Path
from tempfile import TemporaryDirectory
from django.conf import settings
from django.test import SimpleTestCase
from .backups import create_backup,restore_drill,backup_status,inspect_database

class WorldBackupTests(SimpleTestCase):
    def test_old_save_restore_migrates_preserves_facts_and_retains_only_owned_snapshots(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);source=root/'old.sqlite3';dest=root/'snapshots'
            result=subprocess.run([sys.executable,'manage.py','migrate','characters','0014','--noinput'],env=__import__('ore_empire.database',fromlist=['sqlite_environment']).sqlite_environment(source),cwd=settings.BASE_DIR,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr.decode())
            with sqlite3.connect(source) as db:
                db.execute("INSERT INTO auth_user (password,last_login,is_superuser,username,first_name,last_name,email,is_staff,is_active,date_joined) VALUES ('private-hash','2026-01-01',1,'keeper','','','',1,1,'2026-01-01')")
            with sqlite3.connect(source) as db:
                def insert(table,overrides):
                    values={name:(default if default is not None else (None if not required and not primary else 0 if 'INT' in kind else '')) for _,name,kind,required,default,primary in db.execute('PRAGMA table_info('+table+')')}
                    values.update(overrides)
                    db.execute('INSERT INTO '+table+' ('+','.join(values)+') VALUES ('+','.join('?' for _ in values)+')',list(values.values()))
                insert('characters_playerprofile',{'id':1,'user_id':1,'level':1,'life':50,'current_health':50,'max_energy':100,'current_energy':100,'ore_balance':789,'premium_balance':12,'experience':456,'skill_points':9,'camp':'OLD_CAMP','guild':'SHADOW'})
                insert('characters_itemblueprint',{'id':1,'name':'Test sword'})
                insert('characters_owneditem',{'id':1,'owner_id':1,'blueprint_id':1,'is_equipped':1})
            original=inspect_database(source)
            first=create_backup(source,dest,2)
            self.assertFalse(backup_status(dest)['verified_at'])
            restored=root/'drill.sqlite3';restore_drill(first,restored,source)
            self.assertEqual(inspect_database(restored,{k:v['columns'] for k,v in original.items()}),original)
            self.assertTrue(backup_status(dest)['verified_at'])
            self.assertEqual(restored.stat().st_mode&0o777,0o600)
            self.assertNotIn('private-hash',(first/'manifest.json').read_text())
            with self.assertRaises(ValueError):restore_drill(first,source,source)
            with self.assertRaises(ValueError):restore_drill(first,restored,source)
            foreign=dest/'world-not-ours';foreign.mkdir()
            second=create_backup(source,dest,2)
            # Creating verification.json touches the old directory, not its creation manifest.
            os.utime(first,ns=(first.stat().st_atime_ns,second.stat().st_mtime_ns+10_000_000_000))
            self.assertEqual(backup_status(dest)['name'],second.name)
            create_backup(source,dest,2)
            self.assertFalse(first.exists());self.assertTrue(foreign.exists())
            self.assertEqual(backup_status(dest)['count'],2)

    def test_corrupt_backup_cannot_create_restore_or_replace_live_data(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);source=root/'live.sqlite3'
            with sqlite3.connect(source) as db:db.execute('CREATE TABLE example (id INTEGER)')
            # Minimal synthetic database with migration metadata still supports snapshot validation.
            with sqlite3.connect(source) as db:db.execute('CREATE TABLE django_migrations (app TEXT,name TEXT)')
            backup=create_backup(source,root/'copies')
            with open(backup/'world.sqlite3','ab') as stream:stream.write(b'corrupt')
            with self.assertRaisesMessage(ValueError,'checksum'):restore_drill(backup,root/'test.sqlite3',source)
            self.assertFalse((root/'test.sqlite3').exists())
            self.assertTrue(source.exists())

    def test_story_text_upgrade_is_allowed_but_reward_changes_are_detected(self):
        with TemporaryDirectory() as directory:
            source=Path(directory)/'story.sqlite3'
            snapshot={'version':1,'title':'Stary tekst','description':'Opis','rewards':{'ore':12},'objectives':[{'id':'talk','kind':'talk','label':'Etykieta','options':{'stand':'Dawna odpowiedź'}}]}
            with sqlite3.connect(source) as db:
                db.execute('CREATE TABLE characters_storyrun (id INTEGER PRIMARY KEY,snapshot TEXT)')
                db.execute('INSERT INTO characters_storyrun VALUES (1,?)',(json.dumps(snapshot),))
            before=inspect_database(source)
            snapshot['title']='Nowy tekst';snapshot['narrative_version']=2;snapshot['objectives'][0]['options']['stand']='Nowa odpowiedź'
            with sqlite3.connect(source) as db:db.execute('UPDATE characters_storyrun SET snapshot=?',(json.dumps(snapshot),))
            self.assertEqual(inspect_database(source),before)
            snapshot['rewards']['ore']=999
            with sqlite3.connect(source) as db:db.execute('UPDATE characters_storyrun SET snapshot=?',(json.dumps(snapshot),))
            self.assertNotEqual(inspect_database(source),before)

    def test_faction_membership_choice_and_earned_rank_survive_real_restore(self):
        script="""
import django
django.setup()
from django.core.management import call_command
from django.db import transaction
from characters.test_faction_succession import fixture,person,succeed
from characters.faction_choice import choose
from characters.faction_advancement import BY_KEY
from characters.camp_progression import accept_camp_quest,promote_in_camp,record_camp_event
call_command('migrate',interactive=False,verbosity=0)
c,i,race=fixture();p=person(c,'SWAMP_CAMP','TEMPLAR');p.level=45;p.strength=180;p.ore_balance=20000;p.save();succeed(race)
assert choose(p,'BANDITS');rank=BY_KEY['ADV_BANDITS_4'];assert accept_camp_quest(p,rank.key)
for goal in rank.objectives:
    for _ in range(goal.count):
        with transaction.atomic():record_camp_event(p,goal.event)
assert promote_in_camp(p,rank.key)
"""
        from ore_empire.database import sqlite_environment
        with TemporaryDirectory() as directory:
            root=Path(directory);source=root/'new-rank.sqlite3'
            result=subprocess.run([sys.executable,'-c',script],env=sqlite_environment(source),cwd=settings.BASE_DIR,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr.decode())
            before=inspect_database(source)
            for table in ['characters_factionsuccession','characters_factionmembership','characters_factionchoice','characters_factionrankprogress','characters_campquest']:
                self.assertIn(table,before);self.assertEqual(before[table]['count'],1)
            backup=create_backup(source,root/'copies');restored=root/'restored.sqlite3'
            proof=restore_drill(backup,restored,source)
            self.assertTrue(proof['migration_applied']);self.assertEqual(inspect_database(restored),before)
