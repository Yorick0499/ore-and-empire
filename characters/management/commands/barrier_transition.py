from django.core.management import BaseCommand,CommandError
from django.contrib.auth.models import User
from django.db import transaction
from characters.models import SleeperRace,BarrierEvent

class Command(BaseCommand):
    help='Stan, wznowienie i wstrzymanie połączenia po rzeczywistym obozowym zwycięstwie. Bez pomijania finału.'
    def add_arguments(self,p):
        p.add_argument('race',type=int)
        p.add_argument('--operator')
        group=p.add_mutually_exclusive_group();group.add_argument('--pause',action='store_true');group.add_argument('--unpause',action='store_true');group.add_argument('--resume',action='store_true')
    def handle(self,*args,**opts):
        race=SleeperRace.objects.filter(pk=opts['race']).first()
        if not race:raise CommandError('Nieznany wyścig.')
        if any(opts[k] for k in ('pause','unpause','resume')):
            user=User.objects.filter(username=opts['operator'],is_active=True,is_superuser=True).first()
            if not user:raise CommandError('Wymagany aktywny administrator --operator LOGIN.')
            if opts['pause'] or opts['unpause']:
                from characters.barrier_admin import set_paused
                from django.core.exceptions import ValidationError
                try:set_paused(user,race.pk,opts['pause'],race.state)
                except ValidationError as exc:raise CommandError(str(exc)) from exc
            elif opts['resume']:
                from characters.barrier_activation import activate
                if not activate(race.pk):raise CommandError('Przejście nieukończone: sprawdź pauzę, dzierżawę, zwycięstwo, kopie i narzędzia bazy.')
        race.refresh_from_db();self.stdout.write(f'{race.pk}: {race.state}; pauza={race.paused}; zwycięzca={race.winner_id}; backup={bool(race.backup_digest)}')
