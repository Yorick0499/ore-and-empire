"""Per-world fenced scheduler ownership, shared by local and standalone workers."""
from contextlib import contextmanager
from datetime import timedelta
from uuid import uuid4
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Now
from .models import SchedulerLease

class LeaseLost(RuntimeError):
    pass

class SchedulerGuard:
    def __init__(self,world,ttl=60):
        if not 15<=ttl<=300:raise ValueError('Lease TTL must be 15..300 seconds')
        self.world_id=world.pk;self.owner=uuid4();self.ttl=timedelta(seconds=ttl)
    def acquire(self):
        SchedulerLease.objects.get_or_create(world_id=self.world_id)
        changed=SchedulerLease.objects.filter(world_id=self.world_id).filter(Q(owner__isnull=True)|Q(expires_at__lte=Now())).update(owner=self.owner,heartbeat_at=Now(),expires_at=Now()+self.ttl)
        if not changed:raise LeaseLost('Ten świat ma już aktywny scheduler. Nie uruchomiono drugiej pętli botów.')
        return self
    def fence(self):
        # Hold this row through action commit. A successor cannot overlap a slow action.
        row=SchedulerLease.objects.select_for_update().get(world_id=self.world_id)
        if row.owner!=self.owner or not SchedulerLease.objects.filter(pk=row.pk,expires_at__gt=Now()).exists():raise LeaseLost('Utracono dzierżawę schedulera; akcja bota została zatrzymana.')
        SchedulerLease.objects.filter(pk=row.pk).update(heartbeat_at=Now(),expires_at=Now()+self.ttl)
    @contextmanager
    def work(self):
        with transaction.atomic():
            self.fence()
            yield
    def release(self):
        SchedulerLease.objects.filter(world_id=self.world_id,owner=self.owner).update(owner=None,expires_at=Now())
    def __enter__(self):return self.acquire()
    def __exit__(self,*args):self.release()
