"""Idempotent event schedules. No rewards are granted by calendar reads."""
from django.utils import timezone
from .models import WorldEvent
from .world_clock import POLISH_TIME


def active_events(now=None,*,world_ids=None,include_regional=False):
    now = now or timezone.now()
    from .worlds import current_world
    from .barrier import region_ids
    rows=WorldEvent.objects.filter(world_id__in=region_ids(current_world()) if world_ids is None else world_ids,enabled=True, starts_at__lte=now, ends_at__gt=now)
    return rows if include_regional else rows.filter(region='')


def reward_rates(*, events=None):
    events=list(active_events()) if events is None else [e for e in events if not e.region]
    from .world_clock import clock_state
    clock=clock_state()
    return (max([clock['ore'],*(event.ore_percent for event in events)]),
            max([clock['experience'],*(event.experience_percent for event in events)]),
            max([0,*(event.premium_bonus for event in events)]),
            list(dict.fromkeys([clock['name']+' — rytm świata',*[event.name for event in events]])))


def reward_snapshot(ore, experience, premium=0, *, rates=None,profile=None,activity="",target="",consume_key=None,regional_context=None):
    ore_rate,xp_rate,premium_bonus,names=reward_rates() if rates is None else rates
    result=(ore*ore_rate//100,experience*xp_rate//100,premium+premium_bonus if premium else 0,names)
    if profile is not None and activity:
        from .regional_events import enhance
        return enhance(profile,activity,target,ore,experience,result,consume_key,regional_context)
    return result


from django.db import transaction
@transaction.atomic
def ensure_world_events(now=None):
    from .models import World,EventSchedule
    from .worlds import current_world
    from .world_releases import sync_releases
    from .barrier import region_ids,clear_region_cache
    from .regional_events import seed_regional, refresh_regional_text, retire_regional_duplicates, VERSION
    from .event_narratives import stage_for, VERSION as TEXT_VERSION
    from .calendar_events import seed_calendar, retire_joined_duplicates, prefix
    now=(now or timezone.now()).astimezone(POLISH_TIME)
    selected=current_world()
    ids=region_ids(selected)
    canonical=(World.objects.filter(pk__in=ids,is_current=True).first() or selected) if len(ids)>1 else selected
    world=World.objects.select_for_update().get(pk=canonical.pk)
    # The Barrier may have committed while this scheduler waited for the row.
    # Re-read the group under the lock; never lock colony after already locking
    # a formerly separate island, or seed a second calendar after activation.
    clear_region_cache()
    ids=region_ids(world)
    if len(ids)>1 and not world.is_current:return
    flags=sync_releases(world,now)
    stage=stage_for(world.universe,flags)
    cursor,_=EventSchedule.objects.get_or_create(world=world)
    stamp=f"v{VERSION}:text{TEXT_VERSION}:{now.date()}:{','.join(map(str,sorted(ids)))}:{','.join(sorted(flags))}"
    marker=prefix(world.pk)+f'season-window-{now.year}-{now.month}'
    if cursor.stamp==stamp and WorldEvent.objects.filter(key=marker).exists():return
    seed_calendar(world,stage,now)
    if len(ids)>1:
        retire_joined_duplicates(world,ids,now)
        retire_regional_duplicates(world,ids,now)
    refresh_regional_text(world,stage,now)
    seed_regional(world,flags,now)
    cursor.stamp=stamp;cursor.save(update_fields=['stamp'])
