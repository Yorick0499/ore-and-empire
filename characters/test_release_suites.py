"""Bounded simulation selection, isolation and backwards-compatible reports."""
import json,tempfile
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from django.core.management import call_command,CommandError
from django.test import SimpleTestCase
from .management.commands.simulate_release import SUITES,FULL_CASES

class ReleaseSuiteTests(SimpleTestCase):
    def test_quick_selects_only_quick_checks_and_uses_private_sqlite(self):
        with tempfile.TemporaryDirectory() as folder:
            report=Path(folder)/'quick.json'
            with patch('characters.management.commands.simulate_release.subprocess.run',return_value=SimpleNamespace(returncode=0)) as run:
                call_command('simulate_release',report=str(report),suite='quick',stdout=StringIO())
            data=json.loads(report.read_text());args=run.call_args
            self.assertEqual(data['suite'],'quick');self.assertEqual(data['test_labels'],SUITES['quick'])
            self.assertEqual(args.args[0][2:],['test',*SUITES['quick'],'--noinput'])
            self.assertEqual(args.kwargs['env']['ORE_DATABASE_ENGINE'],'sqlite')
            self.assertEqual(args.kwargs['env']['DATABASE_URL'],'')
            self.assertEqual(Path(args.kwargs['env']['ORE_DATABASE_PATH']).name,'isolated.sqlite3')
            self.assertEqual(data['time_models'],{});self.assertEqual(data['scenarios'],[])
            self.assertFalse(any('playtest_' in case or 'test_campaign' in case for case in data['test_labels']))
    def test_default_full_retains_all_previous_scenarios_and_report_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            report=Path(folder)/'full.json'
            with patch('characters.management.commands.simulate_release.subprocess.run',return_value=SimpleNamespace(returncode=0)):
                call_command('simulate_release',report=str(report),stdout=StringIO())
            data=json.loads(report.read_text())
            self.assertEqual(data['schema'],2);self.assertEqual(data['suite'],'full')
            self.assertTrue(set(FULL_CASES)<=set(data['test_labels']))
            self.assertTrue({'regression','pacing','personas'}<=set(data['time_models']))
            self.assertTrue(data['isolated_database']);self.assertTrue(data['success'])
    def test_failed_child_writes_failed_report_and_raises_error(self):
        with tempfile.TemporaryDirectory() as folder:
            report=Path(folder)/'failure.json'
            with patch('characters.management.commands.simulate_release.subprocess.run',return_value=SimpleNamespace(returncode=1)):
                with self.assertRaises(CommandError):call_command('simulate_release',report=str(report),suite='pacing',stdout=StringIO())
            data=json.loads(report.read_text());self.assertFalse(data['success'])
            self.assertEqual(set(data['time_models']),{'pacing'})
    def test_invalid_suite_and_existing_report_cannot_start_tests_or_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            report=Path(folder)/'keep.json';report.write_text('keep')
            with patch('characters.management.commands.simulate_release.subprocess.run') as run:
                with self.assertRaises(CommandError):call_command('simulate_release',report=str(report),suite='quick',stdout=StringIO())
                with self.assertRaises(CommandError):call_command('simulate_release',report=str(report),suite='unknown',stdout=StringIO())
                run.assert_not_called()
            self.assertEqual(report.read_text(),'keep')
