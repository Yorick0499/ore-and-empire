"""Explicit server and character context. One playable server per installation."""
from django.core.exceptions import PermissionDenied
from .models import World,PlayerProfile


def current_world():
    from .realms import _scope
    scoped=_scope.get()
    if scoped:
        selected=World.objects.filter(pk=scoped).first()
        if selected:return selected
    world=World.objects.filter(is_current=True).first()
    if world:return world
    return World.objects.create(is_current=True)


def profile_for(user):
    world=current_world()
    cached=getattr(user,"_server_profile",None)
    if cached is not None and cached.user_id==user.pk and cached.world_id==world.pk:
        return cached
    profile=PlayerProfile.objects.filter(user=user,world=world,is_draft=False).order_by('slot').first()
    profile=profile or PlayerProfile.objects.filter(user=user,world=world,is_draft=True).first()
    if not profile:
        used=set(user.characters.values_list('slot',flat=True))
        slot=next((n for n in range(1,6) if n not in used),None)
        if slot is None:raise PermissionDenied('Wybierz istniejącą postać w kreatorze.')
        profile=PlayerProfile.objects.create(user=user,world=world,slot=slot)
        from .economic_ledger import record_opening
        record_opening(profile)
    user._server_profile=profile
    return profile


def playable(profile):
    world=profile.world
    from .realms import is_open
    from .models import SleeperRace
    from django.db.models import Q
    from django.utils import timezone
    merging=SleeperRace.objects.filter(Q(colony_id=profile.world_id)|Q(khorinis_id=profile.world_id),state='merging',lease_expires_at__gt=timezone.now()).exists()
    return not merging and not profile.is_draft and is_open(world)


def world_context(request):
    world=current_world()
    from .world_clock import clock_state
    from .barrier import joined,region
    profile=getattr(request.user,'_server_profile',None) if request.user.is_authenticated else None
    visited=region(profile) if profile and not request.path.startswith('/zarzadca/') else world
    return {'world_joined':joined(world), 'visited_region':visited, 'is_khorinis':visited.universe=='GOTHIC_II','realm_title':'Khorinis' if visited.universe=='GOTHIC_II' else 'Kolonia','active_character':getattr(request.user,'_server_profile',None) if request.user.is_authenticated else None,'world_clock':clock_state(),'server_world':visited,'world_needs_setup':not world.configured}
