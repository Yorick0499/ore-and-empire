from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from . import game_logic as game
from .models import AdventureTemplate, AdventureRun, ItemBluePrint, OwnedItem, PremiumEntry
from .adventures import ADVENTURES, ADVENTURE_DETAILS, CATEGORIES, choose_adventure
from .adventure_browse import adventure_context
from .economy import start_adventure, claim_adventure
from .equipment import add_item


class ContractTests(TestCase):
    def setUp(self):
        call_command('seed_adventures',stdout=StringIO())
        self.p=User.objects.create_user('zleceniobiorca').playerprofile
        self.client.force_login(self.p.user)

    def test_full_pool_diverse_from_first_level_and_preserves_admin_edits(self):
        self.assertEqual(len(ADVENTURES),44)
        self.assertEqual(AdventureTemplate.objects.count(),44)
        self.assertEqual(len({q[0] for q in ADVENTURES}),44)
        self.assertEqual(set(ADVENTURE_DETAILS),{q[0] for q in ADVENTURES})
        self.assertEqual(set(AdventureTemplate.objects.filter(level=0).values_list('category',flat=True)),dict(CATEGORIES).keys())
        for q in AdventureTemplate.objects.all():
            q.full_clean()
            self.assertTrue(q.place and q.success_text)
            self.assertTrue(1<=q.energy_cost<=28)
            self.assertTrue(45<=q.duration_seconds<=900)
        q=AdventureTemplate.objects.get(key='mine_lamps');q.name='Dostawa operatora';q.category='watch';q.ore_reward=17;q.enabled=False;q.success_text='Zapis operatora';q.save()
        call_command('seed_adventures',stdout=StringIO());q.refresh_from_db()
        self.assertEqual((q.name,q.category,q.ore_reward,q.enabled,q.success_text),('Dostawa operatora','watch',17,False,'Zapis operatora'))
        self.assertEqual(AdventureTemplate.objects.count(),44)

    def test_cost_time_and_reward_styles_offer_real_tradeoffs(self):
        jobs={q.key:q for q in AdventureTemplate.objects.filter(level=0)}
        self.assertLess(jobs['scavenger_tracks'].duration_seconds,jobs['mine_lamps'].duration_seconds)
        self.assertGreater(jobs['scavenger_tracks'].experience_reward,jobs['mine_lamps'].experience_reward)
        self.assertLess(jobs['scavenger_tracks'].ore_reward,jobs['mine_lamps'].ore_reward)
        self.assertLess(jobs['lake_watch'].energy_cost,jobs['scavenger_tracks'].energy_cost)
        self.assertGreater(jobs['lake_watch'].duration_seconds,jobs['scavenger_tracks'].duration_seconds)
        self.assertTrue(AdventureTemplate.objects.filter(level=30).exists())

    def test_accepted_briefing_and_rewards_survive_template_changes_and_replay(self):
        q=AdventureTemplate.objects.get(key='tavern_nets');run=start_adventure(self.p,q.pk)
        expected=(run.ore_reward,run.experience_reward,run.premium_reward);briefing=run.briefing.copy()
        q.name='NOWY TYTUŁ';q.description='Nowa treść';q.category='watch';q.place='Inne miejsce';q.success_text='Inny finał';q.ore_reward=999999;q.enabled=False;q.save()
        self.assertContains(self.client.get('/zadania/?category=scout&q=brak'),briefing['name'])
        self.assertNotContains(self.client.get('/zadania/?category=scout&q=brak'),'NOWY TYTUŁ')
        other=User.objects.create_user('inny').playerprofile
        with patch('django.utils.timezone.now',return_value=run.ends_at):
            self.assertFalse(claim_adventure(other,run.pk))
            before=(self.p.ore_balance,self.p.experience,self.p.premium_balance)
            self.assertTrue(claim_adventure(self.p,run.pk))
            self.assertFalse(claim_adventure(self.p,run.pk))
            self.p.refresh_from_db()
            self.assertEqual((self.p.ore_balance,self.p.experience,self.p.premium_balance),tuple(a+b for a,b in zip(before,expected)))
            page=self.client.get('/zadania/?q=brak')
            self.assertContains(page,briefing['success_text'])
            self.assertNotContains(page,'Inny finał')
            self.assertFalse(PremiumEntry.objects.filter(profile=self.p,reference=f'adventure:{run.pk}').exists()) # zero shard job
        run.refresh_from_db();self.assertEqual(run.briefing,briefing)

    def test_future_claim_level_gate_energy_gate_and_busy_do_not_charge(self):
        q=AdventureTemplate.objects.get(key='pass_courier')
        self.assertFalse(start_adventure(self.p,q.pk))
        q=AdventureTemplate.objects.get(key='courier')
        self.p.current_energy=4;self.p.save()
        self.assertFalse(start_adventure(self.p,q.pk))
        self.p.current_energy=100;self.p.save();run=start_adventure(self.p,q.pk)
        balance=(self.p.ore_balance,self.p.experience,self.p.premium_balance,self.p.current_energy)
        self.assertFalse(claim_adventure(self.p,run.pk));self.assertFalse(start_adventure(self.p,q.pk))
        self.p.refresh_from_db();self.assertEqual(balance,(self.p.ore_balance,self.p.experience,self.p.premium_balance,self.p.current_energy))

    def test_filters_pagination_and_active_run_are_independent(self):
        self.assertEqual(adventure_context(self.p,{})['quest_count'],6)
        for query in ['światło','ŚWIATŁO','Światło']:
            self.assertEqual(adventure_context(self.p,{'q':query})['quest_count'],1)
        self.assertEqual(adventure_context(self.p,{'q':'.*'})['quest_count'],0)
        c=adventure_context(self.p,{'access':'all','page':'2','category':'scout','q':'','sort':'short'})
        self.assertTrue(all(row['quest'].category=='scout' for row in c['quests']))
        c=adventure_context(self.p,{'access':'all','page':'2'})
        self.assertEqual(len(c['quests']),20);self.assertIn('access=all',c['quest_pager']['previous_url'])
        c=adventure_context(self.p,{'q':'Cavalorna'})
        self.assertEqual(c['quest_count'],0)
        c=adventure_context(self.p,{'q':'Cavalorna','access':'all'})
        self.assertEqual(c['quest_count'],1);self.assertFalse(c['quests'][0]['available'])
        q=AdventureTemplate.objects.get(key='courier');run=start_adventure(self.p,q.pk)
        c=adventure_context(self.p,{'q':'nieistniejące'})
        self.assertEqual(c['run'].pk,run.pk)
        response=self.client.post('/zadania/?category=delivery&sort=short',{'action':'claim','run':run.pk,'ore_reward':99999})
        self.assertEqual(response.url,'/zadania/?category=delivery&sort=short')
        run.refresh_from_db();self.assertIsNone(run.claimed_at)

    def test_reward_preview_uses_one_event_query_for_whole_page(self):
        self.p.level=30;self.p.save()
        with CaptureQueriesContext(connection) as queries:c=adventure_context(self.p,{'access':'all'})
        event_selects=[q for q in queries if 'characters_worldevent' in q['sql']]
        self.assertEqual(len(event_selects),1)
        self.assertEqual(len(c['quests']),24)
        for row in c['quests']:self.assertGreaterEqual(row['experience'],row['quest'].experience_reward)

    def test_role_rotation_and_real_services_for_each_category(self):
        self.p.is_bot=True;self.p.bot_role='hunter';self.p.save()
        selected=set()
        for turn in range(8):
            self.p.bot_turn=turn;selected.add(choose_adventure(self.p).category)
        self.assertEqual(selected,{'scout','watch'})
        first=choose_adventure(self.p)
        run=start_adventure(self.p,first.pk)
        with patch('django.utils.timezone.now',return_value=run.ends_at+timedelta(seconds=1)):
            self.assertTrue(claim_adventure(self.p,run.pk))
            self.p.bot_turn+=2;self.p.save()
            self.assertNotEqual(choose_adventure(self.p).pk,first.pk)
        self.p.is_bot=False;self.p.save();now=timezone.now()
        for n,(category,label) in enumerate(CATEGORIES):
            with patch('django.utils.timezone.now',return_value=now+timedelta(hours=n)):
                game.refresh_player(self.p)
                q=AdventureTemplate.objects.filter(category=category,level=0).first()
                run=start_adventure(self.p,q.pk);self.assertIsInstance(run,AdventureRun)
            with patch('django.utils.timezone.now',return_value=now+timedelta(hours=n,minutes=10)):
                self.assertTrue(claim_adventure(self.p,run.pk))
        self.assertEqual(self.p.adventures.filter(claimed_at__isnull=False).count(),len(CATEGORIES)+1)


class RarityPresentationTests(TestCase):
    def setUp(self):
        self.p=User.objects.create_user('zbrojmistrz').playerprofile
        self.other=User.objects.create_user('kupiec').playerprofile
        self.client.force_login(self.p.user)
        self.bp=ItemBluePrint.objects.create(name='Łowcy Śniącego [I]',damage=20,base_value=60,source_game='GOTHIC_I')
        self.items=[add_item(self.p,self.bp,rarity=i) for i in range(5)]

    def test_all_rarities_have_card_frames_and_distinct_named_badges(self):
        from .enhancements import QUALITY_RANKS
        page=self.client.get('/ekwipunek/')
        for rank in QUALITY_RANKS:
            self.assertContains(page,'rarity-card rarity-'+rank['key'])
            self.assertContains(page,'quality-badge quality-'+rank['key'])
            self.assertContains(page,rank['name'])
        self.assertContains(page,'rarity-seal')
        for route in ['/ekwipunek/','/sklep/','/przedmioty/']:
            response=self.client.get(route,{'q':'łOWCY śNIĄCEGO [i]'})
            self.assertContains(response,self.bp.name)
        self.assertEqual(self.client.get('/ekwipunek/',{'q':'.*'}).context['player_inventory'].paginator.count,0)
        self.assertContains(self.client.get('/sklep/'),'rarity-card rarity-runic')
        self.assertContains(self.client.get(f'/ekwipunek/{self.items[4].pk}/porownaj/'),'rarity-card rarity-ancient')

    def test_frame_follows_equipped_and_listed_instance_not_blueprint(self):
        self.assertTrue(game.equip_item(self.p,self.items[3]))
        self.items[3].refresh_from_db()
        self.assertContains(self.client.get('/ekwipunek/'),'rarity-card rarity-runic')
        self.assertTrue(game.list_item_on_market(self.p,self.items[4],50))
        page=self.client.get('/plac_targowy/')
        self.assertContains(page,'rarity-card rarity-ancient')
        self.assertContains(page,'quality-badge quality-ancient')
        self.assertEqual(self.client.get('/plac_targowy/',{'q':'łowcy śniącego [i]'}).context['market_all_items'].paginator.count,1)
        self.assertEqual(self.client.get('/plac_targowy/',{'q':'.*'}).context['market_all_items'].paginator.count,0)
        # Original blueprint on NPC stock has no rolled instance rarity.
        q=self.client.get('/sklep/?kind=weapon')
        self.assertNotContains(q,'Towary</h2><article class="colony-panel rarity-card')


class BriefingMigrationTests(TestCase):
    def test_legacy_run_keeps_custom_title_deadline_rewards_and_ownership(self):
        import subprocess, sys, tempfile
        from pathlib import Path
        from django.conf import settings
        from ore_empire.database import sqlite_environment
        with tempfile.TemporaryDirectory(prefix='ore-briefing-migration-') as folder:
            env=sqlite_environment(Path(folder)/'world.sqlite3')
            def execute(*args):
                result=subprocess.run([sys.executable,*args],cwd=settings.BASE_DIR,env=env,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr[-3000:])
            execute('manage.py','migrate','--noinput')
            execute('manage.py','migrate','characters','0037','--noinput')
            execute('-c',"""
import os
os.environ['DJANGO_SETTINGS_MODULE']='ore_empire.settings'
import django;django.setup()
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from datetime import timedelta
apps=MigrationExecutor(connection).loader.project_state([('characters','0037_rzadkosc_lupow_i_kuznia_plus_trzy')]).apps
U=apps.get_model('auth','User');P=apps.get_model('characters','PlayerProfile');W=apps.get_model('characters','World');T=apps.get_model('characters','AdventureTemplate');R=apps.get_model('characters','AdventureRun')
u=U.objects.create(username='legacy-probe');w=W.objects.first();w.name='Kopia testowa';w.save()
p=P.objects.create(user=u,world=w);q=T.objects.create(key='courier',name='Nazwa operatora',description='Własna treść',ore_reward=17)
R.objects.create(profile=p,template=q,ends_at=timezone.now()+timedelta(days=1),ore_reward=13,experience_reward=71,premium_reward=0,event_names=['Dawna premia'])
from characters.migration_testing import historical_fixture
from characters.management.commands.import_sqlite_world import EXCLUDES
import json
rows=json.loads(historical_fixture(apps,EXCLUDES))
run=next(row for row in rows if row['model']=='characters.adventurerun')
assert run['fields']['ore_reward']==13 and 'briefing' not in run['fields']
assert 'category' not in next(row for row in rows if row['model']=='characters.adventuretemplate')['fields']

""")
            execute('manage.py','migrate','--noinput')
            execute('-c',"""
import os
os.environ['DJANGO_SETTINGS_MODULE']='ore_empire.settings'
import django;django.setup()
from characters.models import AdventureRun
r=AdventureRun.objects.select_related('template').get()
assert r.public_name=='Nazwa operatora' and r.public_description=='Własna treść'
assert (r.ore_reward,r.experience_reward,r.premium_reward)==(13,71,0)
assert r.event_names==['Dawna premia'] and r.claimed_at is None
assert r.profile.user.username=='legacy-probe' and r.briefing['category']=='delivery'
assert r.template.ore_reward==17
old=r.public_name;r.template.name='Zmienione';r.template.save();r.refresh_from_db()
assert r.public_name==old
""")


class LegacyProofTests(TestCase):
    def test_legacy_pg_proof_ignores_only_added_narrative_columns(self):
        import json
        from .management.commands.import_sqlite_world import canonical
        old=[{'model':'characters.adventurerun','pk':1,'fields':{'ore_reward':17,'template':2}},
             {'model':'characters.adventuretemplate','pk':2,'fields':{'name':'Dawny tytuł','ore_reward':17}}]
        new=json.loads(json.dumps(old))
        new[0]['fields']['briefing']={'name':'Dawny tytuł'}
        new[1]['fields'].update(category='delivery',place='Trakt',success_text='Dostarczono')
        self.assertEqual(canonical(json.dumps(old)),canonical(json.dumps(new),legacy_adventures=True))
        self.assertNotEqual(canonical(json.dumps(old)),canonical(json.dumps(new)))
        new[0]['fields']['ore_reward']=18
        self.assertNotEqual(canonical(json.dumps(old)),canonical(json.dumps(new),legacy_adventures=True))
