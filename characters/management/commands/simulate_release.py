"""Runs real gameplay on Django's isolated test database, never the user's save."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError

class Command(BaseCommand):
    help='Przejście kampanii gracza i trzech obozów botów oraz próby nadużyć w osobnej bazie testowej.'
    def add_arguments(self,parser):
        parser.add_argument('--report',required=True,help='Nowy plik raportu JSON; istniejące pliki nie są nadpisywane.')
    def handle(self,*args,**options):
        target=Path(options['report']).resolve()
        if target.exists():raise CommandError('Raport już istnieje; wybierz nową ścieżkę.')
        start=time.monotonic()
        with tempfile.TemporaryDirectory(prefix='ore-release-probe-') as tmp:
            facts=Path(tmp)/'facts.json';facts.write_text('[]')
            from ore_empire.database import sqlite_environment
            env={**sqlite_environment(Path(tmp)/'isolated.sqlite3'),'ORE_PROBE_REPORT':str(facts)}
            cases=['characters.test_khorinis','characters.test_new_progression','characters.test_campaign.CampaignTests.test_human_can_play_whole_campaign_via_forms_and_ordinary_game_services','characters.test_campaign.CampaignTests.test_every_camp_bot_can_finish_from_new_character_without_runtime_grants','characters.test_release_abuse','characters.test_world_clock','characters.test_release_finale','characters.test_polish_time','characters.test_endgame','characters.test_bug_audit','characters.test_bot_policies','characters.test_item_protection','characters.test_market_browse','characters.test_equipment_comparison','characters.test_rarity','characters.test_solo_playability','characters.test_adventure_variety','characters.playtest_scenarios','characters.playtest_pacing','characters.playtest_postmerge','characters.test_bot_personalities','characters.test_market_intelligence','characters.test_bot_cycle_simulation']
            result=subprocess.run([sys.executable,str(settings.BASE_DIR/'manage.py'),'test',*cases,'--noinput'],cwd=settings.BASE_DIR,env=env)
            scenarios=json.loads(facts.read_text())
            report={
                'schema':2,'success':result.returncode==0,
                'elapsed_seconds':round(time.monotonic()-start,2),
                'isolated_database':True,
                'world_clock':'Europe/Warsaw; rzeczywisty dzień słoneczny Warszawy',
                'test_labels':cases,'recorded_scenarios':len(scenarios),'scenarios':scenarios,
                'time_models':{
                    'regression':'Kampanie: 30 minut na krok; trzy buildy: 15 minut. To kroki testowe, nie czas przejścia.',
                    'pacing':'Osobne tempo-kampanii: 10 sekund na próbę akcji, rzeczywiste timery i regeneracja; sesje ciągłe lub godzina dziennie.',
                    'personas':'48 godzin co 5 minut, z jawnymi limitowanymi symulowanymi zakupami premium botów.',
                },
                'limits':[
                    'Automatyczne przejścia łączą formularze i zwykłe serwisy; osobny test Chromium sprawdza GUI.',
                    'Tempo kampanii jest modelem strategii wojownika, nie pomiarem czasu człowieka ani całego G2 NK.',
                    'Raport nie zastępuje testów współbieżności PostgreSQL ani publicznego hostingu.',
                ],
            }
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('x') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        self.stdout.write(str(target))
        if result.returncode:raise CommandError('Wykryto błąd przejścia; szczegóły w wynikach testów i raporcie.')
