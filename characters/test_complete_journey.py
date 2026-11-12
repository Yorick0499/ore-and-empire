"""Release rehearsal isolation, earned-finale navigation and runtime location coverage."""
import json,tempfile
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from django.core.management import call_command,CommandError
from django.test import SimpleTestCase,TestCase

class FullJourneyCommandTests(SimpleTestCase):
    def test_command_uses_disposable_file_db_and_cannot_inherit_private_pg(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=Path(tmp)/'journey.json'
            with patch('characters.management.commands.simulate_journey.subprocess.run',return_value=SimpleNamespace(returncode=0)) as child:
                call_command('simulate_journey',report=report,stdout=StringIO())
            args=child.call_args;env=args.kwargs['env']
            self.assertEqual(args.args[0][1:],['-m','characters.playtest_full_journey'])
            self.assertEqual(env['DATABASE_URL'],'');self.assertEqual(env['ORE_DATABASE_ENGINE'],'sqlite')
            self.assertEqual(env['ORE_DATABASE_PATH'],env['ORE_JOURNEY_DATABASE']);self.assertTrue(Path(env['ORE_JOURNEY_DATABASE']).parent.name.startswith('ore-complete-journey-'))
            self.assertFalse(Path(env['ORE_JOURNEY_DATABASE']).parent.exists());self.assertTrue(json.loads(report.read_text())['success'])
    def test_failed_child_writes_report_and_existing_report_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=Path(tmp)/'journey.json'
            with patch('characters.management.commands.simulate_journey.subprocess.run',return_value=SimpleNamespace(returncode=1)):
                with self.assertRaises(CommandError):call_command('simulate_journey',report=report,stdout=StringIO())
            old=report.read_bytes();self.assertFalse(json.loads(old)['success'])
            with patch('characters.management.commands.simulate_journey.subprocess.run') as child:
                with self.assertRaises(CommandError):call_command('simulate_journey',report=report,stdout=StringIO())
                child.assert_not_called()
            self.assertEqual(report.read_bytes(),old)

class RuntimeLocationArtTests(SimpleTestCase):
    def test_every_nk_location_and_boss_has_local_g2_art(self):
        from .gothic_assets import MANIFEST_PATH
        from .locations import LOCATIONS
        from .bosses import BOSSES
        manifest=json.loads(MANIFEST_PATH.read_text())
        for loc in LOCATIONS:
            if loc.universe!='GOTHIC_II' and not loc.post_barrier:continue
            self.assertEqual(manifest[loc.key]['game'],'GOTHIC_II_NK',loc.key)
            if loc.key in BOSSES:self.assertEqual(manifest[loc.key+'_boss']['game'],'GOTHIC_II_NK',loc.key)
        from .locations import BY_KEY
        self.assertEqual(BY_KEY['g2nk_inubis'].wiki,'Krypta Inubisa')
    def test_exact_jarkendar_photo_is_not_marked_as_a_generic_placeholder(self):
        from .templatetags.gothic_media import gothic_art
        self.assertFalse(gothic_art('jark_swamp')['illustrative'])
        self.assertTrue(gothic_art('g2nk_forest')['illustrative'])
    def test_pinned_locations_match_manifest_and_sources(self):
        from .gothic_assets import MANIFEST_PATH
        manifest=json.loads(MANIFEST_PATH.read_text())
        rules=json.loads((Path(__file__).parent/'data/gothic2-location-art.json').read_text())['locations']
        for key,row in rules.items():
            self.assertEqual(manifest[key]['selected_file'],row['file']);self.assertEqual(manifest[key]['source_revision'],row['revision'])

class FinaleNavigationTests(TestCase):
    def setUp(self):
        from .test_faction_succession import fixture,person,succeed
        self.c,self.i,race=fixture();call_command('seed_khorinis',stdout=StringIO());self.p=person(self.c,'OLD_CAMP','BARON');self.p.level=45;self.p.save();succeed(race)
        self.client.force_login(self.p.user)
    def test_nk_finale_prioritizes_repeatable_game_and_keeps_old_progress(self):
        from .testing_story import claimed_milestone
        from .player_journey import journey
        from .models import FrontierProgress
        claimed_milestone(self.p,'nk-undead');FrontierProgress.objects.create(profile=self.p,unlocked=17,wins=25)
        context=journey(self.p);self.assertTrue(context['nk_complete']);self.assertIn('NK ukończona',context['steps'][1]['title'])
        response=self.client.get('/warty/');self.assertContains(response,'Warty wspólnych szlaków');self.assertContains(response,'Irdorath');self.assertNotContains(response,'Świat pozostaje w Gothic I')
        self.assertEqual(FrontierProgress.objects.get(profile=self.p).unlocked,17)
    def test_pre_barrier_khorinis_patrol_never_claims_to_be_in_colony(self):
        from .models import World
        from .frontier import presentation
        World.objects.filter(pk__in=[self.c.pk,self.i.pk]).update(union_key=None)
        self.p.world=self.i;self.p.save(update_fields=['world']);self.assertEqual(presentation(self.p)['title'],'Warty Khorinis')
