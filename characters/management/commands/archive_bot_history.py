from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from characters.world_monitor import archive_decisions

class Command(BaseCommand):
    help='Archive old raw bot decisions to private gzip JSONL and preserve daily aggregates.'
    def add_arguments(self,parser):
        parser.add_argument('--days',type=int,default=30)
        parser.add_argument('--directory',default=str(settings.BASE_DIR/'telemetry-archives'))
    def handle(self,*args,**options):
        try:result=archive_decisions(options['directory'],options['days'])
        except (ValueError,OSError) as exc:raise CommandError(str(exc)) from exc
        self.stdout.write(str(result))
