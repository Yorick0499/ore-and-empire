from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from characters.backups import restore_drill

class Command(BaseCommand):
    help='Restore and migrate into a NEW test database; never overwrites the live world.'
    def add_arguments(self,parser):
        parser.add_argument('backup')
        parser.add_argument('--target')
        parser.add_argument('--target-database')
    def handle(self,*args,**options):
        from django.db import connection
        try:
            if connection.vendor=='postgresql':
                if not options['target_database'] or options['target']:raise ValueError('Użyj --target-database z nową nazwą bazy.')
                from characters.postgres_backups import restore_pg_drill
                proof=restore_pg_drill(options['backup'],options['target_database'])
            else:
                if not options['target'] or options['target_database']:raise ValueError('Użyj --target z nową ścieżką SQLite.')
                proof=restore_drill(options['backup'],options['target'],settings.DATABASES['default']['NAME'])
        except Exception as exc:raise CommandError('Próba odtworzenia odmówiona lub nieudana; źródłowa kopia i żywa baza pozostają nienaruszone.') from exc
        self.stdout.write(self.style.SUCCESS(f"Restore verified: {proof['tables']} tables; isolated destination. Live database unchanged."))
