import json,os,subprocess,sys,tempfile
from pathlib import Path
from django.conf import settings
from django.db import connection
from django.core.management import BaseCommand,CommandError

class Command(BaseCommand):
    help='Real PostgreSQL race tests and 100 bots with concurrent player requests; separate test DB.'
    def add_arguments(self,parser):parser.add_argument('--report',required=True,type=Path)
    def handle(self,*args,**options):
        target=options['report']
        if connection.vendor!='postgresql' or target.exists():raise CommandError('Wymagany PostgreSQL oraz nowy plik raportu.')
        with tempfile.TemporaryDirectory(prefix='ore-pg-load-') as tmp:
            facts=Path(tmp)/'facts.json';facts.write_text('[]')
            process=subprocess.run([sys.executable,str(settings.BASE_DIR/'manage.py'),'test','characters.test_concurrency','--noinput'],cwd=settings.BASE_DIR,env={**os.environ,'ORE_PROBE_REPORT':str(facts)})
            report={'schema':1,'engine':'postgresql','isolated_test_database':True,'success':process.returncode==0,'scenarios':json.loads(facts.read_bytes()),'limits':['Krótka próba lokalna, nie prognoza wydajności hostingu ani wielodniowej gospodarki.']}
            target.parent.mkdir(parents=True,exist_ok=True)
            with open(target,'x') as stream:json.dump(report,stream,ensure_ascii=False,indent=2)
        if process.returncode:raise CommandError('Scenariusze współbieżności nie przeszły.')
