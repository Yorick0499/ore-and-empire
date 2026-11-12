"""Run selected organic build journeys in a disposable SQLite test database."""
import json,subprocess,sys,tempfile,time
from pathlib import Path
from django.conf import settings
from django.core.management import BaseCommand,CommandError
from ore_empire.database import sqlite_environment

class Command(BaseCommand):
    help='Organiczne buildy i frakcje od0 do NK, rangi8 i endgame; osobna baza, globalna Bariera jako zdarzenie zewnętrzne.'
    def add_arguments(self,parser):
        from characters.playtest_build_journeys import CASES
        parser.add_argument('--report',required=True,type=Path)
        parser.add_argument('--case',action='append',choices=tuple(CASES),dest='cases')
    def handle(self,*args,**options):
        from characters.playtest_build_journeys import CASES
        target=options['report'].resolve()
        if target.exists():raise CommandError('Raport istnieje; wybierz nowy plik.')
        cases=list(dict.fromkeys(options['cases'] or CASES))
        start=time.monotonic()
        with tempfile.TemporaryDirectory(prefix='ore-build-journeys-') as tmp:
            root=Path(tmp);facts=root/'facts.json';facts.write_text('[]')
            env={**sqlite_environment(root/'world.sqlite3'),'ORE_PROBE_REPORT':str(facts)}
            labels=['characters.playtest_build_journeys.EarnedBuildJourneys.test_'+key.replace('-','_') for key in cases]
            result=subprocess.run([sys.executable,'manage.py','test',*labels,'--noinput'],cwd=settings.BASE_DIR,env=env)
            scenarios=json.loads(facts.read_text())
            done={r['case'] for r in scenarios if r['scenario']=='earned-build-faction-journey'}
            success=result.returncode==0 and done==set(cases)
            report={'schema':1,'success':success,'seconds':round(time.monotonic()-start,2),'isolated_database':True,'cases':cases,'completed':sorted(done),'scenarios':scenarios,'limits':['Earned character progression; external global community victory, separately verified by simulate_journey.','Virtual timers, knowledgeable strategy, no competing player market/PvP or long economy.']}
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('x') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        self.stdout.write(str(target))
        if not success:raise CommandError('Macierz buildów nie przeszła; sprawdź log i raport.')
