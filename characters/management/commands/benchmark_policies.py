"""Compare ordinary bot play on two copies of one synthetic save. Never touches live data."""
import argparse,io,json,os,random,shutil,subprocess,sys,tempfile,time,urllib.request
from collections import Counter
from datetime import datetime,timedelta,timezone as utc
from pathlib import Path
from unittest.mock import patch
from django.conf import settings
from django.core.management import BaseCommand,CommandError,call_command
from django.db.models import Sum
from ore_empire.database import sqlite_environment

class Command(BaseCommand):
    help='Isolated rule-vs-local-model comparison; local Ollama must already have the selected model.'
    def add_arguments(self,parser):
        parser.add_argument('--report',type=Path,required=True)
        parser.add_argument('--model',default='qwen2.5:0.5b')
        parser.add_argument('--endpoint',default='http://127.0.0.1:11434/api/chat')
        parser.add_argument('--steps',type=int,default=100)
        parser.add_argument('--calls',type=int,default=8)
        parser.add_argument('--timeout',type=float,default=5)
        parser.add_argument('--case',choices=['setup','baseline','ollama'],help=argparse.SUPPRESS)
    def handle(self,*args,**opts):
        from characters.bot_policies import OllamaPolicy
        if not 20<=opts['steps']<=300 or not 1<=opts['calls']<=20 or not .1<=opts['timeout']<=5:raise CommandError('Niepoprawny limit benchmarku.')
        # Validate endpoint/cloud exclusions before any warmup or child process.
        candidate=OllamaPolicy(opts['model'],endpoint=opts['endpoint'],timeout=opts['timeout'],max_calls=opts['calls'],max_tokens=(4096+48)*opts['calls'],max_seconds=opts['calls']*opts['timeout']+1)
        if opts['case']:
            if os.environ.get('ORE_BENCH_WORKER')!='1':raise CommandError('Tryb wewnętrzny wymaga odizolowanego procesu benchmarku.')
            self.run_case(opts,candidate);return
        target=opts['report']
        if target.exists():raise CommandError('Raport już istnieje; wybierz nową ścieżkę.')
        started=time.monotonic();warmup=False
        from characters.local_model_transport import NoRedirect
        try:
            payload={'model':opts['model'],'messages':[],'stream':False,'keep_alive':'5m','options':{'num_gpu':0,'num_thread':2,'num_predict':1}}
            request=urllib.request.Request(opts['endpoint'],data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect()).open(request,timeout=30) as response:warmup=response.status==200
        except Exception:pass
        warmup_seconds=round(time.monotonic()-started,3)
        with tempfile.TemporaryDirectory(prefix='ore-policy-comparison-') as tmp:
            root=Path(tmp);source=root/'seed.sqlite3';base_env={**sqlite_environment(source),'ORE_BENCH_WORKER':'1'}
            common=[sys.executable,str(settings.BASE_DIR/'manage.py'),'benchmark_policies','--model',opts['model'],'--endpoint',opts['endpoint'],'--steps',str(opts['steps']),'--calls',str(opts['calls']),'--timeout',str(opts['timeout'])]
            setup=subprocess.run([*common,'--case','setup','--report',str(root/'setup.json')],cwd=settings.BASE_DIR,env=base_env,capture_output=True)
            if setup.returncode:raise CommandError('Nie udało się przygotować izolowanego świata porównawczego.')
            records={}
            for case in ('baseline','ollama'):
                db=root/(case+'.sqlite3');shutil.copyfile(source,db);db.chmod(0o600);report=root/(case+'.json')
                result=subprocess.run([*common,'--case',case,'--report',str(report)],cwd=settings.BASE_DIR,env={**sqlite_environment(db),'ORE_BENCH_WORKER':'1'},capture_output=True)
                if result.returncode:raise CommandError('Scenariusz benchmarku nie powiódł się: '+case)
                records[case]=json.loads(report.read_bytes())
            evaluated=records['ollama']['model_statuses'].get('accepted',0)>0
            result={'schema':1,'isolated_databases':True,'synthetic_equal_start':True,'model':opts['model'],'model_evaluated':evaluated,'warmup':{'ok':warmup,'seconds':warmup_seconds,'included_in_policy_budget':False},'budget':{'max_calls':opts['calls'],'timeout_seconds':opts['timeout'],'gpu_layers':0,'inference_threads':2,'paid_api_cost':0},'cases':records,'limits':['Jedna krótka próba na trzech botach, nie dowód przewagi LLM ani wielodniowej stabilności gospodarki.','Ten sam zapis i ziarno startowe; odmienne decyzje zmieniają kolejne losowania. Czas przyspieszony o 30 minut na krok, bez grantów.','Warmup jest osobnym, jawnym kosztem lokalnego modelu. Wywołania polityki są ograniczone wspólnym budżetem próby.']}
            target.parent.mkdir(parents=True,exist_ok=True)
            with open(target,'x') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
        self.stdout.write('Zapisano izolowane porównanie. Domyślnej polityki świata nie zmieniono.')
    def run_case(self,opts,policy):
        from characters.models import PlayerProfile,World,BattleRecord,MarketTrade,BotDecision
        from characters.bots import tick_bot
        from characters.economic_ledger import summary
        if opts['case']=='setup':
            output=io.StringIO()
            call_command('migrate',stdout=output)
            for command in ('seed_world','seed_equipment','seed_catalog','seed_adventures'):call_command(command,stdout=output)
            call_command('run_bots',create=3,create_only=True,stdout=output)
            World.objects.filter(is_current=True).update(configured=True,bot_count=3,name='Porównanie polityk')
            return
        random.seed(19);start=datetime(2026,11,7,7,tzinfo=utc.utc);started=time.monotonic();actions=Counter();failures=0
        bots=list(PlayerProfile.objects.filter(is_bot=True).order_by('pk'))
        for step in range(opts['steps']):
            with patch('django.utils.timezone.now',return_value=start+timedelta(minutes=30*step)):
                for bot in bots:
                    action,success=tick_bot(bot,policy if opts['case']=='ollama' else None,force_active=True);actions[action]+=1;failures+=int(not success)
        model_rows=[row for row in BotDecision.objects.filter(policy_version='ollama-1').values_list('policy_snapshot',flat=True)]
        result={'policy':'baseline-20' if opts['case']=='baseline' else 'ollama-1','steps':opts['steps'],'bots':len(bots),'elapsed_seconds':round(time.monotonic()-started,3),'actions':dict(actions),'failed_actions':failures,'experience':PlayerProfile.objects.aggregate(total=Sum('experience'))['total'] or 0,'levels':list(PlayerProfile.objects.order_by('pk').values_list('level',flat=True)),'battles':BattleRecord.objects.count(),'wins':BattleRecord.objects.filter(won=True).count(),'trades':MarketTrade.objects.count(),'economy':summary()['resources'],'model_statuses':dict(Counter(row.get('status','unknown') for row in model_rows)),'model_latency_ms':round(sum(row.get('latency_ms',0) for row in model_rows),2),'prompt_tokens':sum(row.get('prompt_tokens',0) for row in model_rows),'generated_tokens':sum(row.get('generated_tokens',0) for row in model_rows)}
        opts['report'].write_text(json.dumps(result,ensure_ascii=False,indent=2))
