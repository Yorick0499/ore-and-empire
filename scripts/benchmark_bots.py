#!/usr/bin/env python3
"""Linux local benchmark with a disposable world, real scheduler and real HTTP."""
import argparse
import json
import os
from pathlib import Path
import socket
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser();parser.add_argument('--report',required=True);parser.add_argument('--seconds',type=int,default=45);parser.add_argument('--mature',action='store_true')
args=parser.parse_args();target=Path(args.report).resolve()
if target.exists():raise SystemExit('Raport już istnieje.')
if not 20<=args.seconds<=300:raise SystemExit('--seconds: 20–300')
with tempfile.TemporaryDirectory(prefix='ore-100-bots-') as tmp:
    os.environ['ORE_DATABASE_PATH']=str(Path(tmp)/'world.sqlite3');os.environ.setdefault('DJANGO_SETTINGS_MODULE','ore_empire.settings');sys.path.insert(0,str(ROOT))
    import django
    django.setup()
    from django.core.management import call_command
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from characters.world_management import seed_clean_world
    from characters.models import PlayerProfile,World,BotDecision
    from characters.bots import tick_bot
    from characters.worlds import current_world
    from io import StringIO
    quiet=StringIO();call_command('migrate',interactive=False,stdout=quiet);seed_clean_world()
    world=current_world();world.configured=True;world.bot_count=100;world.save()
    call_command('run_bots',create=100,create_only=True,limit=100,stdout=quiet)
    bots=list(PlayerProfile.objects.filter(is_bot=True).order_by('pk'))
    if args.mature:
        from characters.models import CampaignCompletion,BossAttempt,ItemBluePrint
        from characters.equipment import add_item
        from characters import game_logic as game
        # Controlled performance fixture only, never claimed to be a real campaign run.
        for bot in bots:
            bot.level=30;bot.strength=200;bot.life=500;bot.current_health=500;bot.camp='OLD_CAMP';bot.ore_balance=2000;bot.save()
            attempt=BossAttempt.objects.create(profile=bot,boss_key='sleeper_sanctum',won=True)
            CampaignCompletion.objects.create(profile=bot,battle=attempt)
            for kind in ('onehand','armor'):
                game.equip_item(bot,add_item(bot,ItemBluePrint.objects.get(catalog_key='colony-loot-4-'+kind)))
    times=[];queries=[];actions={}
    # Warm every account through two genuine decisions, then measure the live loop.
    for bot in bots:
        from django.db import reset_queries
        reset_queries()
        start=time.perf_counter()
        with CaptureQueriesContext(connection) as captured:action,ok=tick_bot(bot)
        times.append(time.perf_counter()-start);queries.append(len(captured));actions[action]=actions.get(action,0)+1
        if not ok:raise RuntimeError((bot.pk,action))
    connection.close()
    with socket.socket() as listener:listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
    env={**os.environ,'PYTHONUNBUFFERED':'1'}
    with open(Path(tmp)/'server.log','w') as log:
        from django.utils import timezone
        live_started=timezone.now()
        process=subprocess.Popen([sys.executable,str(ROOT/'play.py'),'--bots','100','--port',str(port)],cwd=ROOT,env=env,stdout=log,stderr=log)
        try:
            url=f'http://127.0.0.1:{port}/konto/logowanie/'
            ready=False
            for _ in range(150):
                if process.poll() is not None:raise RuntimeError('Launcher zakończył się przed testem.')
                try:
                    with urllib.request.urlopen(url,timeout=1) as response:ready=response.status==200
                    if ready:break
                except OSError:time.sleep(.1)
            if not ready:raise RuntimeError('Brak odpowiedzi HTTP.')
            def cpu():
                fields=Path(f'/proc/{process.pid}/stat').read_text().split()
                return (int(fields[13])+int(fields[14]))/os.sysconf('SC_CLK_TCK')
            rss=[];latencies=[];errors=0;started=time.monotonic();cpu_start=cpu()
            while time.monotonic()-started<args.seconds:
                start=time.perf_counter()
                try:
                    with urllib.request.urlopen(url,timeout=5) as response:
                        if response.status!=200:errors+=1
                except OSError:errors+=1
                latencies.append(time.perf_counter()-start)
                for line in Path(f'/proc/{process.pid}/status').read_text().splitlines():
                    if line.startswith('VmRSS:'):rss.append(int(line.split()[1])/1024)
                time.sleep(.1)
            elapsed=time.monotonic()-started;cpu_used=cpu()-cpu_start
            def percentile(values,fraction):return sorted(values)[min(len(values)-1,int(len(values)*fraction))]
            facts={'schema':1,'isolated_database':True,'population':100,'fixture':('100 kontrolowanych buildów poziomu 30 po finale; nadane statystyki służą wyłącznie pomiarowi wydajności, nie walidacji przejścia' if args.mature else '100 nowych kont botów, zwykłe akcje bez nadawania statystyk; lokalny launcher i żądania ekranu logowania'),'elapsed_seconds':round(elapsed,2),'http_requests':len(latencies),'http_errors':errors,'http_p50_ms':round(statistics.median(latencies)*1000,2),'http_p95_ms':round(percentile(latencies,.95)*1000,2),'http_max_ms':round(max(latencies)*1000,2),'cpu_percent_one_core':round(cpu_used/elapsed*100,2),'rss_peak_mib':round(max(rss),2),'initial_tick_p50_ms':round(statistics.median(times)*1000,2),'initial_tick_p95_ms':round(percentile(times,.95)*1000,2),'initial_queries_median':statistics.median(queries),'initial_actions':actions,'limits':['Pomiar na maszynie wykonującej test, nie na komputerze gracza.','Krótka próba lokalnego SQLite i ekranu logowania; nie zastępuje obciążenia publicznego serwera ani długiej symulacji gospodarki.','Cel adaptacyjnego harmonogramu około 20% czasu pracy nie jest twardym limitem CPU.']}
        finally:
            process.terminate()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.wait()
    from django.db.models import Max,Min,Count
    facts['residents_ticked']=PlayerProfile.objects.filter(is_bot=True,bot_last_tick__gte=live_started).count()
    facts['resident_turns']=list(PlayerProfile.objects.filter(is_bot=True).values('bot_turn').annotate(count=Count('pk')).order_by('bot_turn'))
    facts['failed_decisions']=BotDecision.objects.filter(success=False).count()
    if errors or facts['failed_decisions']:raise RuntimeError('Błędy HTTP lub decyzji botów.')
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(facts,ensure_ascii=False))
