from characters.bot_population import DEFAULT_BOTS_PER_WORLD, MAX_BOTS_PER_WORLD
from io import StringIO
from django.core.management import BaseCommand,CommandError,call_command
from django.db import transaction
from characters.models import World,CampGuild
from characters.realms import world_scope
from characters.khorinis import CAMPS

class Command(BaseCommand):
    help='Otwórz równoległe Khorinis bez zmieniania Kolonii i dorobku. Ponowienie niczego nie resetuje.'
    def add_arguments(self,p):
        p.add_argument('--bots',type=int,default=DEFAULT_BOTS_PER_WORLD);p.add_argument('--name',default='Latarnia — Khorinis')
    @transaction.atomic
    def handle(self,*args,**opts):
        if not 0<=opts['bots']<=MAX_BOTS_PER_WORLD or not opts['name'].strip() or len(opts['name'])>80:raise CommandError('Niepoprawna nazwa lub liczba botów.')
        primary=World.objects.select_for_update().filter(is_current=True,configured=True,status='active').first()
        if not primary:raise CommandError('Najpierw skonfiguruj Kolonię.')
        existing=World.objects.filter(is_open=True,universe='GOTHIC_II').first()
        if existing:self.stdout.write('Khorinis już otwarte; zachowano ustawienia i postęp.');return
        call_command('seed_khorinis',stdout=self.stdout)
        world=World.objects.create(name=opts['name'].strip(),edition=2,universe='GOTHIC_II',is_open=True,configured=True,bot_count=opts['bots'])
        for camp in CAMPS:CampGuild.objects.create(world=world,camp=camp)
        with world_scope(world):
            if opts['bots']:call_command('run_bots',create=opts['bots'],create_only=True,limit=opts['bots'],stdout=self.stdout)
            from characters.world_events import ensure_world_events
            ensure_world_events()
        self.stdout.write('Otworzono Khorinis. Jarkendar, smoki i NK nadal zamknięte; Kolonia bez zmian.')
