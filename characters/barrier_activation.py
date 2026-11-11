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
    if race is None:return SleeperRace.objects.get(pk=race_id).state=='joined'
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
            from .barrier import unify_mercenaries
            unify_mercenaries(race)
            from .post_barrier import seed
            seed()
            union=uuid5(NAMESPACE_URL,'ore-barrier:'+str(race.pk)+':'+str(race.colony_id))
            World.objects.filter(pk__in=[race.colony_id,race.khorinis_id]).update(union_key=union)
            race.state='joined';race.joined_at=timezone.now();race.backup_path=path;race.backup_digest=digest;race.proof=proof;race.lease_owner=None;race.lease_expires_at=None
            race.save(update_fields=['state','joined_at','backup_path','backup_digest','proof','lease_owner','lease_expires_at'])
            BarrierEvent.objects.create(race=race,kind='joined',details={'backup_digest':digest,'winner':race.winner_id})
        from .market_intelligence import _cache
        _cache.clear()
        return True
    except Exception:
        with transaction.atomic():
            changed=SleeperRace.objects.filter(pk=race.pk,lease_owner=owner).exclude(state='joined').update(state='failed',lease_owner=None,lease_expires_at=timezone.now()+timedelta(seconds=60))
            if changed:BarrierEvent.objects.create(race_id=race.pk,kind='activation_failed')
        return False


def activate_pending():
    # No administrator or client can supply a winning camp or bypass its proof.
    for pk in SleeperRace.objects.filter(state__in=['pending','failed','merging'],paused=False).values_list('pk',flat=True):activate(pk)
