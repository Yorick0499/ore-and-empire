from django.http import JsonResponse
from django.db import connection,DatabaseError
from django.db.models.functions import Now
from .models import World,SchedulerLease

def live(request):return JsonResponse({'status':'ok'})

def ready(request):
    try:
        with connection.cursor() as cursor:cursor.execute('SELECT 1');cursor.fetchone()
        from .models import SleeperRace
        if SleeperRace.objects.filter(state='merging',lease_expires_at__gt=Now()).exists():return JsonResponse({'status':'barrier-transition'},status=503)
        world=World.objects.filter(is_current=True,status='active',configured=True).first()
        if not world:return JsonResponse({'status':'setup-required'},status=503)
        from .realms import open_worlds
        needed=open_worlds().filter(configured=True,bot_count__gt=0)
        active=not needed.exclude(pk__in=SchedulerLease.objects.filter(owner__isnull=False,expires_at__gt=Now()).values('world_id')).exists()
        return JsonResponse({'status':'ready' if active else 'scheduler-unavailable'},status=200 if active else 503)
    except DatabaseError:return JsonResponse({'status':'database-unavailable'},status=503)
