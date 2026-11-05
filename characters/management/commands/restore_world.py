from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from characters.backups import restore_drill

class Command(BaseCommand):
    help='Restore and migrate into a NEW test database; never overwrites the live world.'
    def add_arguments(self,parser):
        parser.add_argument('backup')
        parser.add_argument('--target',required=True)
    def handle(self,*args,**options):
        if settings.DATABASES['default']['ENGINE']!='django.db.backends.sqlite3':raise CommandError('SQLite restore drills only; use PostgreSQL native tools for PostgreSQL.')
        try:proof=restore_drill(options['backup'],options['target'],settings.DATABASES['default']['NAME'])
        except (ValueError,OSError,KeyError) as exc:raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Restore verified: {proof['tables']} tables; migrated copy at {options['target']}. Live database unchanged."))
