from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from characters.item_catalog import PACK_PATH, install_catalog


class Command(BaseCommand):
    help = 'Install the offline Gothic item pack; never reset active balance/admin edits.'
    def add_arguments(self,parser):
        parser.add_argument('--pack',type=Path,default=PACK_PATH)
    def handle(self,*args,**options):
        try:
            pack,created=install_catalog(options['pack'].read_bytes())
        except Exception as exc: raise CommandError(f'Catalog unchanged: {exc}') from exc
        self.stdout.write(f'{pack.game} pack v{pack.version}: {pack.item_count} identities; {created} new blueprints; sha256 {pack.sha256}.')
