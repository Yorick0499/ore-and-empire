import getpass
from django.core.management import BaseCommand,CommandError
from django.core.exceptions import ValidationError,PermissionDenied
from characters.world_management import initialize_world

class Command(BaseCommand):
    help='Initialize one world with an operator password entered privately, never as a CLI argument.'
    def add_arguments(self,parser):
        parser.add_argument('--name',required=True)
        parser.add_argument('--username',required=True)
        parser.add_argument('--bots',type=int,default=100)
    def handle(self,*args,**options):
        first=getpass.getpass('Hasło administratora: ');second=getpass.getpass('Powtórz hasło: ')
        if first!=second:raise CommandError('Hasła nie są zgodne.')
        try:initialize_world(options['name'],options['bots'],options['username'],first)
        except (ValidationError,PermissionDenied) as exc:raise CommandError('Inicjalizacja odmówiona. Sprawdź wymagania hasła, nazwę, liczbę botów i czy świat jest już skonfigurowany.') from exc
        self.stdout.write('Utworzono świat i konto operatora. Hasło nie zostało zapisane w plikach ani wypisane.')
