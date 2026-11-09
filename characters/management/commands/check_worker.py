from django.core.management import BaseCommand,CommandError
from django.db.models.functions import Now
from characters.models import World,SchedulerLease

class Command(BaseCommand):
    help='Exit nonzero when the configured world lacks a live scheduler lease.'
    def handle(self,*args,**options):
        world=World.objects.filter(is_current=True,configured=True,status='active').first()
        from characters.realms import open_worlds
        needed=open_worlds().filter(configured=True,bot_count__gt=0)
        if not world or needed.exclude(pk__in=SchedulerLease.objects.filter(owner__isnull=False,expires_at__gt=Now()).values('world_id')).exists():raise CommandError('Scheduler niedostępny.')
        self.stdout.write('Scheduler gotowy.')
