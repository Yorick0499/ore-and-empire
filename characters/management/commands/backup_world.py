from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from characters.backups import create_backup

class Command(BaseCommand):
    help='Create a consistent private SQLite snapshot (default retention: seven complete backups).'
    def add_arguments(self,parser):
        parser.add_argument('--directory',default=str(settings.BASE_DIR/'backups'))
        parser.add_argument('--keep',type=int,default=7)
    def handle(self,*args,**options):
        from django.db import connection
        try:
            if connection.vendor=='postgresql':
                from characters.postgres_backups import create_pg_backup
                path=create_pg_backup(options['directory'],options['keep'])
            else:path=create_backup(settings.DATABASES['default']['NAME'],options['directory'],options['keep'])
        except Exception as exc:raise CommandError('Nie udało się utworzyć prywatnej kopii. Sprawdź dostęp do bazy, katalogu i klienta PostgreSQL.') from exc
        self.stdout.write(str(path))
