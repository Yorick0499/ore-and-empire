from django.core.management import BaseCommand,CommandError
from django.db.models.functions import Now
from characters.models import World,SchedulerLease

class Command(BaseCommand):
    help='Exit nonzero when the configured world lacks a live scheduler lease.'
    def handle(self,*args,**options):
        world=World.objects.filter(is_current=True,configured=True,status='active').first()
        if not world or not SchedulerLease.objects.filter(world=world,owner__isnull=False,expires_at__gt=Now()).exists():raise CommandError('Scheduler niedostępny.')
        self.stdout.write('Scheduler gotowy.')
