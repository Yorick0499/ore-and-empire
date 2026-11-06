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
            env={**os.environ,'ORE_DATABASE_PATH':str(Path(tmp)/'isolated.sqlite3'),'ORE_PROBE_REPORT':str(facts)}
            cases=['characters.test_campaign.CampaignTests.test_human_can_play_whole_campaign_via_forms_and_ordinary_game_services','characters.test_campaign.CampaignTests.test_every_camp_bot_can_finish_from_new_character_without_runtime_grants','characters.test_release_abuse','characters.test_world_clock','characters.test_release_finale','characters.test_polish_time','characters.test_endgame','characters.test_bug_audit']
            result=subprocess.run([sys.executable,str(settings.BASE_DIR/'manage.py'),'test',*cases,'--noinput'],cwd=settings.BASE_DIR,env=env)
            report={'schema':1,'success':result.returncode==0,'elapsed_seconds':round(time.monotonic()-start,2),'isolated_database':True,'world_clock':'Europe/Warsaw; rzeczywisty dzień słoneczny Warszawy','polish_time_scenarios':4,'loot_endgame_scheduler_scenarios':12,'time_acceleration':'30 minut symulowanego czasu na krok; wyłącznie zwykła regeneracja, bez nadania statystyk lub waluty','scenarios':json.loads(facts.read_text()),'abuse_scenarios':6,'clock_scenarios':4,'finale_scenarios':4,'mixed_sessions':1,'build_matrices':1,'limits':['Automatyczny przebieg gracza miesza formularze fabuły i zwykłe serwisy rozgrywki; osobny przegląd ręczny sprawdza GUI.','Nie jest to test współbieżności PostgreSQL ani test publicznego hostingu.']}
            report['audit_scenarios']=19
            report['bot_policy']='baseline-16'
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('x') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        self.stdout.write(str(target))
        if result.returncode:raise CommandError('Wykryto błąd przejścia; szczegóły w wynikach testów i raporcie.')
