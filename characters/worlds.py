"""Explicit server and character context. One playable server per installation."""
from django.core.exceptions import PermissionDenied
from .models import World,PlayerProfile


def current_world():
    world=World.objects.filter(is_current=True).first()
    if world:return world
    return World.objects.create(is_current=True)


def profile_for(user):
    world=current_world()
    cached=getattr(user,"_server_profile",None)
    if cached is not None and cached.world_id==world.pk:return cached
    profile=PlayerProfile.objects.filter(user=user,world=world).first()
    if not profile:
        profile=PlayerProfile.objects.create(user=user,world=world)
        from .economic_ledger import record_opening
        record_opening(profile)
    user._server_profile=profile
    return profile


def playable(profile):
    world=profile.world
    return world.is_current and world.status=='active' and world.universe=='GOTHIC_I'


def world_context(request):
    world=current_world()
    from .world_clock import clock_state
    return {'world_clock':clock_state(),'server_world':world,'world_needs_setup':not world.configured}
