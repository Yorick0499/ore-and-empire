from django.http import JsonResponse
from django.db import connection,DatabaseError
from django.db.models.functions import Now
from .models import World,SchedulerLease

def live(request):return JsonResponse({'status':'ok'})

def ready(request):
    try:
        with connection.cursor() as cursor:cursor.execute('SELECT 1');cursor.fetchone()
        world=World.objects.filter(is_current=True,status='active',configured=True).first()
        if not world:return JsonResponse({'status':'setup-required'},status=503)
        active=not world.bot_count or SchedulerLease.objects.filter(world=world,owner__isnull=False,expires_at__gt=Now()).exists()
        return JsonResponse({'status':'ready' if active else 'scheduler-unavailable'},status=200 if active else 503)
    except DatabaseError:return JsonResponse({'status':'database-unavailable'},status=503)
