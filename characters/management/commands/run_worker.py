"""Production worker: adaptive scheduling, no HTTP, no implicit migrations."""
import signal,time
from django.core.management import BaseCommand,CommandError,call_command
from django.utils import timezone
from characters.models import World,PlayerProfile,AuthRateBucket
from characters.scheduler_lease import SchedulerGuard,LeaseLost
from characters.bot_scheduler import BotScheduler
from characters.bots import tick_bot
from characters.world_clock import polish_day
from characters.world_events import ensure_world_events

class Command(BaseCommand):
    help='Supervised single-owner bot worker. Requires an initialized world and migrated schema.'
    def add_arguments(self,parser):
        parser.add_argument('--interval',type=float,default=5)
        parser.add_argument('--max-ticks',type=int,default=0,help='Optional finite run for staging/tests; zero runs continuously.')
    def handle(self,*args,**options):
        if not 1<=options['interval']<=3600 or not 0<=options['max_ticks']<=100000:raise CommandError('Niepoprawny interwał lub limit tur.')
        world=World.objects.filter(is_current=True,configured=True,status='active').first()
        if not world:raise CommandError('Najpierw wykonaj migracje i inicjalizację świata.')
        stopped=False;old={}
        def stop(*args):
            nonlocal stopped
            stopped=True
        for sig in (signal.SIGTERM,signal.SIGINT):old[sig]=signal.signal(sig,stop)
        try:
            with SchedulerGuard(world) as guard:
                scheduler=BotScheduler(options['interval']);refresh_at=0;heartbeat=0;day=None;ticks=0
                def run(pk):
                    nonlocal ticks
                    p=PlayerProfile.objects.filter(pk=pk,is_bot=True,user__is_active=True).first()
                    if not p:return 'wait',False
                    try:result=tick_bot(p,lease=guard)
                    except LeaseLost:raise
                    except Exception as exc:self.stderr.write('Worker action failed: '+type(exc).__name__);result=('wait',False)
                    ticks+=1;return result
                while not stopped:
                    now=time.monotonic()
                    if now>=heartbeat:
                        with guard.work():pass
                        heartbeat=now+15
                    if now>=refresh_at:
                        world.refresh_from_db()
                        if not world.is_current or world.status!='active':raise LeaseLost('Świat został zatrzymany lub zmieniony.')
                        scheduler.population(PlayerProfile.objects.filter(world=world,is_bot=True,user__is_active=True).order_by('pk').values_list('pk',flat=True)[:world.bot_count]);refresh_at=now+5
                        if day!=polish_day():
                            with guard.work():
                                ensure_world_events()
                                AuthRateBucket.objects.filter(window_started__lt=timezone.now()-timezone.timedelta(days=7)).delete()
                                call_command('archive_bot_history',days=30,stdout=self.stdout)
                            day=polish_day()
                    scheduler.step(run)
                    if options['max_ticks'] and ticks>=options['max_ticks']:break
                    time.sleep(min(.5,max(.01,scheduler.timeout())))
        except LeaseLost as exc:raise CommandError(str(exc)) from exc
        finally:
            for sig,handler in old.items():signal.signal(sig,handler)
