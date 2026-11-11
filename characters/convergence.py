"""Offline preparation for #30. This module never activates a joined world.

World IDs remain region identities. The future activation consumes a fresh,
verified snapshot; a historical READY preparation is not a licence to migrate.
"""
from datetime import timedelta
import json
from pathlib import Path
from uuid import uuid4
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.db.models import Count
from django.db.models.functions import Now
from django.utils import timezone
from .models import World, PlayerProfile, OwnedItem, AdventureRun, RealmConvergence, ConvergenceEvent


class PreparationBusy(ValidationError):
    pass


def authorize(operator):
    if not User.objects.filter(pk=operator.pk,is_active=True,is_superuser=True).exists():
        raise PermissionDenied('Przygotowanie wymaga aktywnego administratora.')


def worlds(colony_id,khorinis_id):
    rows=World.objects.in_bulk([colony_id,khorinis_id])
    colony=rows.get(colony_id);island=rows.get(khorinis_id)
    if (not colony or not island or colony_id==khorinis_id or
        colony.universe!='GOTHIC_I' or island.universe!='GOTHIC_II' or
        not colony.is_current or not island.is_open or
        any(w.status!='active' or not w.configured for w in (colony,island))):
        raise ValidationError('Wymagana aktywna, skonfigurowana Kolonia i otwarte Khorinis.')
    return colony,island


def dry_run(colony_id,khorinis_id):
    """Read-only, observational plan. It is not a transactional inventory snapshot."""
    colony,island=worlds(colony_id,khorinis_id)
    profiles=PlayerProfile.objects.filter(world_id__in=[colony.pk,island.pk])
    return {
        'schema':1,'phase':'separate','observational':True,
        'worlds':[colony.pk,island.pk],'market':'shared','ranking':'shared',
        'identity_policy':'preserve_worlds_as_regions_and_all_record_ids',
        'activity_policy':'preserve_offers_timers_snapshots_rewards_and_cooldowns',
        'accounts':profiles.values('user_id').distinct().count(),
        'characters':profiles.count(),
        'unassigned_origins':profiles.filter(origin_world__isnull=True).count(),
        'mining_jobs':profiles.filter(action_end_time__isnull=False).count(),
        'unclaimed_adventures':AdventureRun.objects.filter(profile__in=profiles,claimed_at__isnull=True).count(),
        'market_offers':OwnedItem.objects.filter(owner__in=profiles,is_market_listed=True).count(),
        'account_slot_conflicts':profiles.values('user_id').annotate(n=Count('pk')).filter(n__gt=5).count(),
        'activation_available':False,'blocked_by':['camp_sleeper_victory','activation_implementation'],
        'jarkendar_open':False,
    }


def event(operation,kind,**details):
    ConvergenceEvent.objects.create(operation=operation,kind=kind,attempt=operation.attempts,details=details)


@transaction.atomic
def plan_preparation(operator,colony_id,khorinis_id):
    authorize(operator)
    # Same order for competing planners; unique source-world constraints are the final guard.
    list(World.objects.select_for_update().filter(pk__in=[colony_id,khorinis_id]).order_by('pk'))
    plan=dry_run(colony_id,khorinis_id)
    if plan['unassigned_origins'] or plan['account_slot_conflicts']:
        raise ValidationError('Najpierw wyjaśnij pochodzenie lub konflikty slotów postaci.')
    operation,created=RealmConvergence.objects.get_or_create(colony_id=colony_id,khorinis_id=khorinis_id,defaults={'operator':operator,'plan':plan})
    if created:event(operation,'planned')
    return operation


@transaction.atomic
def set_paused(operator,operation_id,paused):
    authorize(operator)
    operation=RealmConvergence.objects.select_for_update().get(pk=operation_id)
    if operation.paused!=paused:
        operation.paused=paused;operation.updated_at=timezone.now();operation.save(update_fields=['paused','updated_at'])
        event(operation,'paused' if paused else 'resumed',operator=operator.pk)
    return operation


def snapshot(root):
    """Use existing consistent-backup and isolated-restore implementations."""
    from .backups import create_backup,restore_drill
    if connection.vendor=='postgresql':
        from .postgres_backups import create_pg_backup,restore_pg_drill
        import psycopg
        from psycopg import sql
        backup=create_pg_backup(root)
        target='ore_convergence_'+uuid4().hex
        proof=restore_pg_drill(backup,target)
        # The restore service leaves a successful drill available; this temporary one is ours.
        config=settings.DATABASES['default']
        kwargs={'dbname':config['NAME'],'user':config.get('USER'),'password':config.get('PASSWORD'),'host':config.get('HOST'),'port':config.get('PORT') or 5432,'connect_timeout':5}
        if config.get('OPTIONS',{}).get('sslmode'):kwargs['sslmode']=config['OPTIONS']['sslmode']
        with psycopg.connect(**kwargs,autocommit=True) as db:
            db.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(target)))
    elif connection.vendor=='sqlite':
        backup=create_backup(settings.DATABASES['default']['NAME'],root)
        target=Path(root)/('drill-'+uuid4().hex+'.sqlite3')
        try:proof=restore_drill(backup,target,settings.DATABASES['default']['NAME'])
        finally:target.unlink(missing_ok=True)
    else:raise ValidationError('Nieobsługiwany silnik kopii.')
    manifest=json.loads((backup/'manifest.json').read_text())
    return str(backup),manifest['database_sha256'],{'engine':manifest['engine'],'restore':proof,'facts':manifest.get('facts',{}),'models':manifest.get('models',{}),'logical_sha256':manifest.get('logical_sha256')}


def verify_snapshot(operation):
    from .backups import sha
    backup=Path(operation.backup_path)
    manifest=json.loads((backup/'manifest.json').read_text())
    filename={'sqlite':'world.sqlite3','postgresql':'world.pgdump'}[manifest['engine']]
    if (manifest['schema']!=1 or manifest['database_sha256']!=operation.backup_digest or
        sha(backup/filename)!=operation.backup_digest or
        json.loads((backup/'verification.json').read_text())!=operation.snapshot['restore']):
        raise ValidationError('Kopia lub dowód odtworzenia uległy zmianie.')


@transaction.atomic
def claim_preparation(operator,operation_id,owner):
    authorize(operator)
    operation=RealmConvergence.objects.select_for_update().get(pk=operation_id)
    if operation.paused:raise ValidationError('Przygotowanie jest wstrzymane.')
    plan=dry_run(operation.colony_id,operation.khorinis_id)
    if plan['unassigned_origins'] or plan['account_slot_conflicts']:
        raise ValidationError('Pochodzenie lub sloty postaci wymagają wyjaśnienia.')
    if operation.lease_owner and RealmConvergence.objects.filter(pk=operation.pk,lease_expires_at__gt=Now()).exists():
        raise PreparationBusy('Przygotowanie ma aktywnego wykonawcę.')
    if operation.phase=='ready':
        try:verify_snapshot(operation);return operation,False
        except (OSError,ValueError,KeyError,ValidationError):event(operation,'backup_invalid')
    operation.plan=plan;operation.phase='backing_up';operation.lease_owner=owner
    operation.lease_expires_at=timezone.now()+timedelta(minutes=15)
    operation.attempts+=1;operation.operator=operator;operation.updated_at=timezone.now()
    operation.save(update_fields=['plan','phase','lease_owner','lease_expires_at','attempts','operator','updated_at'])
    event(operation,'snapshot_started')
    return operation,True


@transaction.atomic
def finish_preparation(operation_id,owner,result=None):
    operation=RealmConvergence.objects.select_for_update().get(pk=operation_id)
    if operation.lease_owner!=owner or not RealmConvergence.objects.filter(pk=operation.pk,lease_expires_at__gt=Now()).exists():
        raise PreparationBusy('Dzierżawa wygasła; stary wykonawca nie może zapisać wyniku.')
    if result is not None and not operation.paused:
        operation.backup_path,operation.backup_digest,operation.snapshot=result
        operation.phase='ready';event(operation,'snapshot_verified')
    else:
        operation.phase='failed';event(operation,'snapshot_failed',reason='paused' if operation.paused else 'snapshot_error')
    operation.lease_owner=None;operation.lease_expires_at=None;operation.updated_at=timezone.now()
    operation.save(update_fields=['phase','backup_path','backup_digest','snapshot','lease_owner','lease_expires_at','updated_at'])
    return operation


def prepare(operator,operation_id,directory):
    if connection.in_atomic_block:
        raise ValidationError('Kopię i odtworzenie uruchom poza transakcją aplikacji.')
    owner=uuid4();operation,claimed=claim_preparation(operator,operation_id,owner)
    if not claimed:return operation
    try:result=snapshot(Path(directory).resolve()/str(operation.pk))
    except Exception:
        finish_preparation(operation.pk,owner)
        raise
    return finish_preparation(operation.pk,owner,result)
