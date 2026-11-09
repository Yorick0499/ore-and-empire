"""Explicit per-request/per-action realm scope; no process-global selected world."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from django.db.models import Q

_scope=ContextVar('ore_world_id',default=None)
G1=('OLD_CAMP','NEW_CAMP','SWAMP_CAMP')
G2=('CITY_WATCH','FIRE_ORDER','ONAR_MERCS')

def camps(world):return G2 if world.universe=='GOTHIC_II' else G1

def open_worlds():
    from .models import World
    return World.objects.filter(Q(is_current=True)|Q(is_open=True),status='active',universe__in=['GOTHIC_I','GOTHIC_II'])

def is_open(world):return world.status=='active' and (world.is_current or world.is_open) and world.universe in {'GOTHIC_I','GOTHIC_II'}

@contextmanager
def world_scope(world):
    token=_scope.set(world.pk if hasattr(world,'pk') else world)
    try:yield
    finally:_scope.reset(token)

def profile_scope(fn):
    @wraps(fn)
    def wrapped(profile,*args,**kwargs):
        lease=kwargs.get('lease')
        if lease is not None and lease.world_id!=profile.world_id:
            from .scheduler_lease import LeaseLost
            raise LeaseLost('Dzierżawa innego serwera nie uprawnia do działania.')
        with world_scope(profile.world_id):return fn(profile,*args,**kwargs)
    return wrapped
