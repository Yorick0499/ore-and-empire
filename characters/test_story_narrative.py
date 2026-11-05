from copy import deepcopy
from io import StringIO
from django.apps import apps
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from .models import StoryQuest,StoryRun
from .gothic_campaign import campaign_definitions,CHAPTERS
from .story_narrative import apply_narrative,pack

class ResidentNarrativeTests(TestCase):
    def setUp(self):
        call_command('seed_story',stdout=StringIO())
        self.row=next(row for row in pack()['entries'] if row['key']=='ritual-ready')
        self.quest=StoryQuest.objects.get(key=self.row['key'])
    def old_snapshot(self):
        fields=('key','version','title','description','chapter','level','camp','universe','prerequisites','any_prerequisites','required_choices','objectives','rewards','energy_cost')
        snapshot={field:deepcopy(getattr(self.quest,field)) for field in fields}
        snapshot.update(self.row['before']);snapshot['version']=1
        for option in self.row['options']:
            for goal in snapshot['objectives']:
                if goal['id']==option['goal']:goal['options'][option['key']]=option['before']
        return snapshot
    def test_active_and_completed_snapshots_keep_contract_progress_choices_and_camp(self):
        before=self.old_snapshot()
        for index,status in enumerate(['active','claimed']):
            p=User.objects.create_user('resident'+str(index)).playerprofile;p.camp='OLD_CAMP';p.guild='GUARD';p.save()
            run=StoryRun.objects.create(profile=p,quest=self.quest,snapshot=deepcopy(before),status=status,progress={'waiting':1},choices={'conversation':'stand'})
            apply_narrative(apps);run.refresh_from_db();p.refresh_from_db()
            self.assertEqual(run.snapshot['title'],self.row['after']['title'])
            self.assertEqual(run.snapshot['version'],1);self.assertEqual(run.snapshot['narrative_version'],2)
            for field in ('rewards','energy_cost','prerequisites','level','camp'):self.assertEqual(run.snapshot[field],before[field])
            self.assertEqual((run.status,run.progress,run.choices),(status,{'waiting':1},{'conversation':'stand'}))
            self.assertEqual((p.camp,p.guild),('OLD_CAMP','GUARD'))
            snapshot=deepcopy(run.snapshot);apply_narrative(apps);run.refresh_from_db();self.assertEqual(snapshot,run.snapshot)
    def test_admin_text_or_version_is_preserved_and_seed_does_not_reset_balance(self):
        self.quest.description='Własny tekst administratora';self.quest.version=7;self.quest.rewards={'ore':17};self.quest.save()
        p=User.objects.create_user('custom-reader').playerprofile
        snapshot=self.old_snapshot();snapshot['description']='Własny zaakceptowany tekst'
        run=StoryRun.objects.create(profile=p,quest=self.quest,snapshot=snapshot)
        apply_narrative(apps);call_command('seed_story',stdout=StringIO())
        self.quest.refresh_from_db();run.refresh_from_db()
        self.assertEqual((self.quest.description,self.quest.version,self.quest.rewards),('Własny tekst administratora',7,{'ore':17}))
        self.assertEqual(run.snapshot,snapshot)
    def test_official_legacy_definitions_upgrade_only_text_and_never_grant_again(self):
        self.quest.title=self.row['before']['title'];self.quest.description=self.row['before']['description'];self.quest.version=1;self.quest.rewards={'ore':23};self.quest.save()
        count=StoryRun.objects.count();apply_narrative(apps);self.quest.refresh_from_db()
        self.assertEqual((self.quest.title,self.quest.version,self.quest.rewards),(self.row['after']['title'],2,{'ore':23}))
        self.assertEqual(StoryRun.objects.count(),count)
        self.assertEqual(StoryQuest.objects.count(),41)
    def test_six_chapters_and_journal_explain_personal_duties_and_shared_progress(self):
        self.assertEqual(len(CHAPTERS),6)
        entries={row['key']:row for row in campaign_definitions(1)}
        self.assertIn('mieszkaniec',entries['free-depths']['description'])
        self.assertIn('odpis',entries['lost-almanac']['description'])
        user=User.objects.create_user('journal-reader');self.client.force_login(user)
        self.assertContains(self.client.get('/fabula/'),'IV rozdział nie usuwa cię ze Starego Obozu')
        self.assertContains(self.client.get('/fabula/'),'Wspólne zlecenia, bossowie i rozwój obozu')
