"""One disposable, file-backed world verifies actual Barrier backup and the whole route."""
import json,subprocess,sys,tempfile,time
from pathlib import Path
from django.conf import settings
from django.core.management import BaseCommand,CommandError
from ore_empire.database import sqlite_environment

class Command(BaseCommand):
    help='Kolonia trzech nowych kont → prawdziwy wspólny Śniący i kopia → NK → powtarzalne warty; wyłącznie osobna baza.'
    def add_arguments(self,parser):parser.add_argument('--report',required=True,type=Path)
    def handle(self,*args,**options):
        target=options['report'].resolve()
        if target.exists():raise CommandError('Raport istnieje; wybierz nowy plik.')
        start=time.monotonic()
        with tempfile.TemporaryDirectory(prefix='ore-complete-journey-') as tmp:
            root=Path(tmp);db=root/'world.sqlite3';facts=root/'facts.json';facts.write_text('[]')
            env={**sqlite_environment(db),'ORE_JOURNEY_DATABASE':str(db),'ORE_PROBE_REPORT':str(facts)}
            result=subprocess.run([sys.executable,'-m','characters.playtest_full_journey'],cwd=settings.BASE_DIR,env=env)
            scenarios=json.loads(facts.read_text())
            report={'schema':1,'success':result.returncode==0,'seconds':round(time.monotonic()-start,2),'isolated_file_database':True,'real_barrier_activation':any(r['scenario']=='earned-community-barrier' for r in scenarios),'scenarios':scenarios,'limits':['Model trzech strategii wojownika; wirtualny czas i zwykłe koszty, nie pomiar czasu człowieka.','Bez konkurencji PvP i rynku innych graczy; pozostałe buildy/populację testują oddzielne pakiety.']}
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('x') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        self.stdout.write(str(target))
        if result.returncode:raise CommandError('Pełna droga nie przeszła; sprawdź log i raport.')
