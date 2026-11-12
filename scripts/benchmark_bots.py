#!/usr/bin/env python3
"""Disposable Linux benchmark: two realms, real worker pacing and authenticated HTTP."""
import argparse,hashlib,json,os,platform,random,socket,statistics,subprocess,sys,tempfile,time
from collections import Counter
from io import StringIO
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parent.parent


def percentile(values,fraction):return sorted(values)[min(len(values)-1,int(len(values)*fraction))]


def isolated_environment(database):
    from ore_empire.database import sqlite_environment
    return {**sqlite_environment(database),'DATABASE_URL':'','SECRET_KEY':'isolated-benchmark-only','DEBUG':'False','ALLOWED_HOSTS':'127.0.0.1,localhost','DJANGO_SETTINGS_MODULE':'ore_empire.settings'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--report',required=True)
    parser.add_argument('--seconds',type=int,default=120)
    parser.add_argument('--population',type=int,default=100)
    parser.add_argument('--mode',choices=['stress','sessions'],default='stress')
    parser.add_argument('--mature',action='store_true')
    parser.add_argument('--endgame',action='store_true',help='Jawna fikstura po finale NK; wymaga --joined i --mature.')
    parser.add_argument('--joined',action='store_true',help='Syntetyczne globalne połączenie obu istniejących regionów; bez resetu postaci.')
    args=parser.parse_args()
    if args.endgame and not (args.joined and args.mature):raise SystemExit('--endgame wymaga --joined i --mature')
    target=Path(args.report).resolve()
    if target.exists():raise SystemExit('Raport już istnieje.')
    if not 20<=args.seconds<=300 or not 2<=args.population<=300:raise SystemExit('Wymagane 20–300 sekund oraz 2–300 botów łącznie.')
    sys.path.insert(0,str(ROOT))
    with tempfile.TemporaryDirectory(prefix='ore-population-benchmark-') as tmp:
        folder=Path(tmp);database=folder/'isolated.sqlite3'
        # An empty URL also prevents load_dotenv from restoring a private PG URL.
        os.environ.update(isolated_environment(database))
        import django;django.setup()
        from django.conf import settings
        from django.db import connection,reset_queries
        if connection.vendor!='sqlite' or Path(settings.DATABASES['default']['NAME']).resolve()!=database:
            raise SystemExit('Odmowa: benchmark wymaga swojej tymczasowej bazy SQLite.')
        from django.core.management import call_command
        from django.test import Client
        from django.test.utils import CaptureQueriesContext
        from django.contrib.auth.models import User
        from django.utils import timezone
        from characters.world_management import seed_clean_world
        from characters.worlds import current_world
        from characters.models import World,PlayerProfile,BotDecision
        from characters.bots import tick_bot
        from characters.character_selection import create_character
        random.seed(118)
        quiet=StringIO();call_command('migrate',interactive=False,stdout=quiet);seed_clean_world()
        first=args.population//2;second=args.population-first
        colony=current_world();colony.configured=True;colony.bot_count=first;colony.bot_personality_cycles=args.mode=='sessions';colony.save()
        call_command('run_bots',world=colony.pk,create=first,create_only=True,stdout=quiet)
        call_command('open_khorinis',bots=second,stdout=quiet)
        island=World.objects.get(universe='GOTHIC_II',is_open=True)
        island.bot_personality_cycles=args.mode=='sessions';island.save()
        actors=list(PlayerProfile.objects.filter(is_bot=True).order_by('pk'))
        if args.mature:
            from characters.models import ItemBluePrint
            from characters.equipment import add_item
            from characters import game_logic as game
            for p in actors:
                p.level=30;p.strength=200;p.life=500;p.current_health=500;p.ore_balance=2000
                p.camp='OLD_CAMP' if p.world_id==colony.pk else 'CITY_WATCH';p.guild='GUARD' if p.world_id==colony.pk else 'K2_COMMANDER';p.save()
                for kind in ('onehand','armor'):
                    key='colony-loot-4-'+kind if p.world_id==colony.pk else 'k2-watch-30-'+kind
                    game.equip_item(p,add_item(p,ItemBluePrint.objects.get(catalog_key=key)))
        if args.joined:
            from uuid import uuid4
            from django.apps import apps
            from django.db import transaction
            from characters.models import SleeperRace,CampGuild
            from characters.faction_succession_v1 import apply
            World.objects.filter(pk__in=[colony.pk,island.pk]).update(union_key=uuid4())
            race=SleeperRace.objects.create(colony=colony,khorinis=island,winner=CampGuild.objects.get(world=colony,camp='OLD_CAMP'),state='joined')
            with transaction.atomic():apply(apps,race)
        if args.endgame:
            from characters.testing_story import claimed_milestone
            for p in actors:
                p.level=45;p.experience=250*45*46;p.strength=300;p.life=600;p.current_health=600;p.ore_balance=5000;p.save()
                for key in ('nk-undead','nk-sailing','jark-portal'):claimed_milestone(p,key)
        times=[];queries=[];warm=Counter()
        for turn in range(2):
            for p in actors:
                reset_queries();start=time.perf_counter()
                with CaptureQueriesContext(connection) as captured:action,ok=tick_bot(p,force_active=True)
                if not ok:raise RuntimeError('Nieudana tura przygotowawcza.')
                times.append(time.perf_counter()-start);queries.append(len(captured));warm[action]+=1
        if args.mode=='stress':
            # Performance fixture: every account is initially eligible; resources stay earned.
            PlayerProfile.objects.filter(is_bot=True).update(bot_last_tick=None)
        human=User.objects.create_user('benchmark-resident')
        other=create_character(human,'Mieszkaniec Khorinis',colony.pk if args.joined else island.pk,start_region=island.pk if args.joined else None)
        if args.endgame:
            from characters.factions import enroll
            for p in (human.playerprofile,other):
                p.level=45;p.experience=250*45*46;p.life=600;p.current_health=600;p.ore_balance=5000;p.camp='OLD_CAMP' if p.world_id==colony.pk else 'CITY_WATCH';p.guild='GUARD' if p.world_id==colony.pk else 'K2_COMMANDER';p.save();enroll(p)
                for key in ('nk-undead','nk-sailing','jark-portal'):claimed_milestone(p,key)
        cookies=[]
        for profile in (human.playerprofile,other):
            client=Client();client.force_login(human);session=client.session
            session['active_character']=profile.pk;session.save()
            cookies.append('sessionid='+client.cookies['sessionid'].value)
        actor_ids=[p.pk for p in actors];del actors
        reset_queries();connection.close()
        with socket.socket() as listener:listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
        env={**os.environ,'PYTHONUNBUFFERED':'1'};log_path=folder/'server.log'
        with log_path.open('w') as log:
            process=subprocess.Popen([sys.executable,str(ROOT/'play.py'),'--bots',str(first),'--port',str(port)],cwd=ROOT,env=env,stdout=log,stderr=log)
            try:
                base=f'http://127.0.0.1:{port}'
                for _ in range(200):
                    if process.poll() is not None:raise RuntimeError('Launcher zakończył się przed testem.')
                    try:
                        with urlopen(base+'/konto/logowanie/',timeout=1) as response:
                            if response.status==200:break
                    except OSError:time.sleep(.1)
                else:raise RuntimeError('Brak odpowiedzi launchera.')
                def cpu():
                    fields=Path(f'/proc/{process.pid}/stat').read_text().split()
                    return (int(fields[13])+int(fields[14]))/os.sysconf('SC_CLK_TCK')
                live_started=timezone.now();rss=[];latencies=[];route_times={};errors=[]
                routes=['/','/zadania/','/sklep-odlamkow/','/zycie-kolonii/']+(['/warty/?track=khorinis','/wspolnota/'] if args.endgame else [])
                started=time.monotonic();cpu_start=cpu();n=0
                while time.monotonic()-started<args.seconds:
                    route=routes[n%len(routes)];cookie=cookies[(n//len(routes))%len(cookies)]
                    req=Request(base+route,headers={'Cookie':cookie});start=time.perf_counter()
                    try:
                        with urlopen(req,timeout=10) as response:
                            if response.status!=200 or '/konto/logowanie/' in response.url:errors.append({'route':route,'status':response.status})
                            response.read()
                    except OSError as exc:errors.append({'route':route,'error':type(exc).__name__})
                    elapsed=time.perf_counter()-start;latencies.append(elapsed);route_times.setdefault(route,[]).append(elapsed)
                    for line in Path(f'/proc/{process.pid}/status').read_text().splitlines():
                        if line.startswith('VmRSS:'):rss.append(int(line.split()[1])/1024)
                    n+=1;time.sleep(.1)
                elapsed=time.monotonic()-started;cpu_used=cpu()-cpu_start
            finally:
                process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait()
        # Read after stopping only this disposable launcher, never a second scheduler.
        people=PlayerProfile.objects.filter(pk__in=actor_ids)
        last=list(people.values('world_id','bot_last_tick','bot_turn'))
        ended_at=timezone.now()
        ages=[max(0,(ended_at-p['bot_last_tick']).total_seconds()) for p in last if p['bot_last_tick']]
        facts={
            'schema':2,'isolated_database':True,'engine':'sqlite','population':args.population,
            'python':platform.python_version(),'platform':platform.platform(),
            'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('characters/bot_scheduler.py','characters/bots.py','characters/models.py')},
            'realm_populations':[first,second],'mode':args.mode,'mature_fixture':args.mature,'global_join_fixture':args.joined,'endgame_fixture':args.endgame,
            'duration_seconds':round(elapsed,2),'http_requests':n,'http_errors':errors,
            'started_at':live_started.isoformat(),
            'warmup':'Two forced ordinary decisions per bot before the measured launcher.',
            'http_p50_ms':round(statistics.median(latencies)*1000,2),
            'http_p95_ms':round(percentile(latencies,.95)*1000,2),
            'routes_p95_ms':{k:round(percentile(v,.95)*1000,2) for k,v in route_times.items()},
            'rss_peak_mib':round(max(rss),2),'rss_start_mib':round(rss[0],2),'rss_end_mib':round(rss[-1],2),
            'cpu_percent_one_core':round(cpu_used/elapsed*100,2),
            'initial_tick_p50_ms':round(statistics.median(times)*1000,2),
            'initial_tick_p95_ms':round(percentile(times,.95)*1000,2),
            'initial_queries_median':statistics.median(queries),'initial_actions':dict(warm),
            'residents_ticked':sum(bool(p['bot_last_tick'] and p['bot_last_tick']>=live_started) for p in last),
            'ticked_per_realm':[sum(bool(p['world_id']==w.pk and p['bot_last_tick'] and p['bot_last_tick']>=live_started) for p in last) for w in (colony,island)],
            'failed_decisions':BotDecision.objects.filter(success=False).count(),
            'last_tick_age_p95_seconds':round(percentile(ages,.95),2) if ages else None,
            'oldest_last_tick_seconds':round(max(ages),2) if ages else None,
            'limits':['Krótki lokalny pomiar SQLite, nie SLA ani wielodniowa stabilność gospodarki.',
                      'RSS i CPU obejmują serwer z kolejką i HTTP, bez procesu przygotowania fixture i przeglądarki.',
                      'HTTP jest uwierzytelnione i obejmuje oba światy; brak równoległych klientów.',
                      'Stress wyłącza okna sesji i zeruje początkowy termin tur; zachowuje zwykłą kadencję oraz reguły akcji.',
                      'Mature, jeśli wybrane, nadaje statystyki wyłącznie do pomiaru i nie dowodzi przejścia kampanii.'],
        }
        facts['validation']={'http_ok':not errors,'actions_ok':facts['failed_decisions']==0,
                             'all_residents_ticked':facts['residents_ticked']==args.population}
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('x') as stream:stream.write(json.dumps(facts,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(facts,ensure_ascii=False))
        if errors or facts['failed_decisions']:raise RuntimeError('Benchmark wykrył błędy HTTP lub odrzucone decyzje; zachowano raport diagnostyczny.')
        if args.mode=='stress' and args.seconds>=120 and facts['residents_ticked']!=args.population:
            raise RuntimeError('Nie wszyscy mieszkańcy dostali turę; raport zachowano. Zwiększ czas i sprawdź kolejkę.')


if __name__=='__main__':main()
