"""Operator-only preparation; no switch exists for activating the joined world."""
import json
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand,CommandError
from django.conf import settings
from characters import convergence
from characters.models import RealmConvergence


class Command(BaseCommand):
    help='Domyślnie odczytowy dry-run #30; jawne przygotowanie tworzy prywatną kopię i sprawdza odtworzenie. Nie łączy światów.'
    def add_arguments(self,p):
        p.add_argument('--colony',type=int)
        p.add_argument('--khorinis',type=int)
        p.add_argument('--operator',help='Login aktywnego administratora dla operacji zapisu.')
        p.add_argument('--directory',default=str(settings.BASE_DIR/'backups'/'convergence'))
        action=p.add_mutually_exclusive_group()
        action.add_argument('--prepare',action='store_true')
        action.add_argument('--resume',metavar='UUID')
        action.add_argument('--status',metavar='UUID')
        action.add_argument('--pause',metavar='UUID')
        action.add_argument('--unpause',metavar='UUID')
    def handle(self,*args,**options):
        try:
            if options['status']:
                operation=RealmConvergence.objects.get(pk=options['status'])
            elif options['pause'] or options['unpause']:
                operator=User.objects.get(username=options['operator'])
                operation=convergence.set_paused(operator,options['pause'] or options['unpause'],bool(options['pause']))
            elif options['prepare'] or options['resume']:
                operator=User.objects.get(username=options['operator'])
                operation=(RealmConvergence.objects.get(pk=options['resume']) if options['resume'] else
                    convergence.plan_preparation(operator,options['colony'],options['khorinis']))
                operation=convergence.prepare(operator,operation.pk,options['directory'])
                if operation.phase!='ready':raise ValueError('Przygotowanie nie zakończyło się.')
            else:
                result=convergence.dry_run(options['colony'],options['khorinis'])
                self.stdout.write(json.dumps(result,ensure_ascii=False,sort_keys=True));return
            valid=False
            if operation.phase=='ready':
                try:convergence.verify_snapshot(operation);valid=True
                except (OSError,ValueError,KeyError,convergence.ValidationError):pass
            result={'operation':str(operation.pk),'phase':operation.phase,'paused':operation.paused,'attempts':operation.attempts,'backup_valid':valid,'activation_available':False}
        except Exception as exc:
            raise CommandError('Operacja odmówiona lub nieudana. Sprawdź światy, administratora, dzierżawę i prywatne kopie; szczegóły są w dzienniku przygotowania. Światy nie zostały połączone.') from exc
        self.stdout.write(json.dumps(result,ensure_ascii=False,sort_keys=True))
