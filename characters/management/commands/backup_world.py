from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from characters.backups import create_backup

class Command(BaseCommand):
    help='Create a consistent private SQLite snapshot (default retention: seven complete backups).'
    def add_arguments(self,parser):
        parser.add_argument('--directory',default=str(settings.BASE_DIR/'backups'))
        parser.add_argument('--keep',type=int,default=7)
    def handle(self,*args,**options):
        if settings.DATABASES['default']['ENGINE']!='django.db.backends.sqlite3':raise CommandError('PostgreSQL requires pg_dump and a separate restore drill; this command supports SQLite only.')
        try:path=create_backup(settings.DATABASES['default']['NAME'],options['directory'],options['keep'])
        except (ValueError,OSError) as exc:raise CommandError(str(exc)) from exc
        self.stdout.write(str(path))
