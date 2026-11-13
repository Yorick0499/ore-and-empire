"""Fenced, restartable activation. A fresh backup is verified under database write locks."""
from datetime import timedelta
import json,os,subprocess,sys
from pathlib import Path
from uuid import uuid4,uuid5,NAMESPACE_URL
from django.conf import settings
from django.db import connection,transaction
from django.db.models.functions import Now
from django.utils import timezone
from .models import World,SleeperRace,BarrierEvent


@transaction.atomic
def claim(race_id,owner):
    race=SleeperRace.objects.select_for_update().get(pk=race_id)
    if race.state=='joined' or race.state=='racing' or race.paused:return None
    if SleeperRace.objects.filter(pk=race.pk,lease_expires_at__gt=Now()).exists():return None
    if not race.winner or not race.sieges.filter(guild=race.winner,health=0,completed_at__isnull=False).exists():raise ValueError('Brak potwierdzonego zwycięstwa.')
    siege=race.sieges.get(guild=race.winner)
    if siege.strikes.filter(damage__gt=0).values('account_id').distinct().count()<3:raise ValueError('Brak wkładu trzech kont.')
    race.state='merging';race.lease_owner=owner;race.lease_expires_at=timezone.now()+timedelta(minutes=10)
    race.save(update_fields=['state','lease_owner','lease_expires_at'])
    BarrierEvent.objects.create(race=race,kind='activation_started')
    return race


def fresh_snapshot(root):
    # Use a separate connection/process: PG backup exports its own read-only snapshot.
    # The caller holds SHARE locks, so no application write can slip into this snapshot.
    config=settings.DATABASES['default']
    if connection.vendor=='sqlite':
        from .convergence import snapshot
        return snapshot(root)
    from .postgres_backups import pg_env
    env={**pg_env(config),'DATABASE_URL':'','DJANGO_SETTINGS_MODULE':'ore_empire.settings'}
    code="import django,json,sys;django.setup();from characters.convergence import snapshot;print(json.dumps(snapshot(sys.argv[1])))"
    result=subprocess.run([sys.executable,'-c',code,str(root)],cwd=settings.BASE_DIR,env=env,capture_output=True,text=True,timeout=480)
    if result.returncode:raise RuntimeError('Nieudana świeża kopia lub próba odtworzenia.')
    return json.loads(result.stdout.strip().splitlines()[-1])


def lock_writes():
    with connection.cursor() as cursor:
        if connection.vendor=='postgresql':
            cursor.execute("SET LOCAL lock_timeout='5s'")
            tables=connection.introspection.table_names(cursor)
            # Includes account/session writes and operator commands, not just player_action.
            cursor.execute('LOCK TABLE '+','.join(connection.ops.quote_name(t) for t in sorted(tables))+' IN SHARE MODE')
        elif connection.vendor=='sqlite':
            # Reserved database writer lock, held until commit. Separate backup reader
            # sees the last committed state, including the durable winning strike.
            cursor.execute('UPDATE characters_world SET rules_version=rules_version WHERE is_current=1')
        else:raise ValueError('Nieobsługiwany silnik bazy.')


def activate(race_id,root=None):
    if connection.in_atomic_block:raise ValueError('Aktywacja wymaga osobnej transakcji.')
    owner=uuid4();race=claim(race_id,owner)
    if race is None:
        return succeed_joined(race_id,root) if SleeperRace.objects.get(pk=race_id).state=='joined' else False
    root=Path(root or settings.BASE_DIR/'backups'/'barrier'/str(race.pk))
    try:
        with transaction.atomic():
            lock_writes()
            race=SleeperRace.objects.select_for_update().get(pk=race.pk)
            if race.paused or race.lease_owner!=owner or not SleeperRace.objects.filter(pk=race.pk,lease_expires_at__gt=Now()).exists():raise ValueError('Wykonawca utracił dzierżawę.')
            regions=list(World.objects.filter(pk__in=[race.colony_id,race.khorinis_id]).order_by('pk'))
            if len(regions)!=2 or any(w.union_key or not w.configured or w.status!='active' for w in regions):raise ValueError('Regiony nie są gotowe do połączenia.')
            path,digest,proof=fresh_snapshot(root)
            if race.lease_owner!=owner or not SleeperRace.objects.filter(pk=race.pk,lease_expires_at__gt=Now()).exists():raise ValueError('Dzierżawa wygasła podczas weryfikacji.')
            from django.apps import apps
            from .faction_succession_v1 import apply
            apply(apps,race)
            from .post_barrier import seed
            seed()
            union=uuid5(NAMESPACE_URL,'ore-barrier:'+str(race.pk)+':'+str(race.colony_id))
            World.objects.filter(pk__in=[race.colony_id,race.khorinis_id]).update(union_key=union)
            from .barrier import clear_region_cache
            clear_region_cache()
            race.state='joined';race.joined_at=timezone.now();race.backup_path=path;race.backup_digest=digest;race.proof=proof;race.lease_owner=None;race.lease_expires_at=None
            race.save(update_fields=['state','joined_at','backup_path','backup_digest','proof','lease_owner','lease_expires_at'])
            BarrierEvent.objects.create(race=race,kind='joined',details={'backup_digest':digest,'winner':race.winner_id})
            from .world_events import ensure_world_events
            from .realms import world_scope
            with world_scope(race.colony):ensure_world_events()
        from .market_intelligence import _cache
        _cache.clear()
        return True
    except Exception:
        from .barrier import clear_region_cache
        clear_region_cache()
        with transaction.atomic():
            changed=SleeperRace.objects.filter(pk=race.pk,lease_owner=owner).exclude(state='joined').update(state='failed',lease_owner=None,lease_expires_at=timezone.now()+timedelta(seconds=60))
            if changed:BarrierEvent.objects.create(race_id=race.pk,kind='activation_failed')
        return False


def activate_pending():
    # No administrator or client can supply a winning camp or bypass its proof.
    from django.db.models import Q
    for pk in SleeperRace.objects.filter(Q(state__in=['pending','failed','merging'])|Q(state='joined',faction_succession__isnull=True),paused=False).values_list('pk',flat=True):activate(pk)


def succeed_joined(race_id,root=None):
    """Upgrade an already joined save behind the same verified-backup fence."""
    from .models import FactionSuccession
    if FactionSuccession.objects.filter(race_id=race_id).exists():return True
    owner=uuid4()
    with transaction.atomic():
        race=SleeperRace.objects.select_for_update().get(pk=race_id)
        if race.state!='joined' or race.paused:return False
        if SleeperRace.objects.filter(pk=race_id,lease_expires_at__gt=Now()).exists():return False
        race.lease_owner=owner;race.lease_expires_at=timezone.now()+timedelta(minutes=10)
        race.save(update_fields=['lease_owner','lease_expires_at'])
    root=Path(root or settings.BASE_DIR/'backups'/'barrier'/str(race_id)/'factions-v1')
    try:
        with transaction.atomic():
            lock_writes()
            race=SleeperRace.objects.select_for_update().get(pk=race_id)
            if FactionSuccession.objects.filter(race=race).exists():return True
            regions=list(World.objects.filter(pk__in=[race.colony_id,race.khorinis_id]))
            if race.paused or race.lease_owner!=owner or race.state!='joined' or len(regions)!=2 or not regions[0].union_key or regions[0].union_key!=regions[1].union_key:raise ValueError('Nieprawidłowy stan sukcesji.')
            path,digest,proof=fresh_snapshot(root)
            from django.apps import apps
            from .faction_succession_v1 import apply
            if not SleeperRace.objects.filter(pk=race_id,lease_owner=owner,lease_expires_at__gt=Now()).exists():raise ValueError('Dzierżawa wygasła podczas weryfikacji.')
            result=apply(apps,race)
            result.details['backup']={'path':path,'digest':digest,'proof':proof};result.save(update_fields=['details'])
            race.lease_owner=None;race.lease_expires_at=None;race.save(update_fields=['lease_owner','lease_expires_at'])
        return True
    except Exception as exc:
        with transaction.atomic():
            changed=SleeperRace.objects.filter(pk=race_id,lease_owner=owner).update(lease_owner=None,lease_expires_at=timezone.now()+timedelta(seconds=60))
            if changed:BarrierEvent.objects.create(race_id=race_id,kind='factions_failed',details={'error':type(exc).__name__})
        return False
