"""Idempotent event schedules. No rewards are granted by calendar reads."""
from datetime import datetime, timedelta, timezone as dt_timezone
import hashlib
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


def _seed_legacy(now=None):
    now = (now or timezone.now()).astimezone(POLISH_TIME)
    from .worlds import current_world
    world=current_world()
    prefix="" if world.pk==1 else f"world-{world.pk}-"
    zone = POLISH_TIME
    for year in (now.year - 1, now.year, now.year + 1):
        for key, name, kind, start, end, ore, experience, premium in (
            ("miners", "Święto Kopaczy", "seasonal", datetime(year, 10, 25, tzinfo=zone), datetime(year, 11, 8, tzinfo=zone), 125, 110, 1),
            ("winter", "Zimowe ogniska kolonii", "holiday", datetime(year, 12, 20, tzinfo=zone), datetime(year + 1, 1, 6, tzinfo=zone), 110, 125, 1),
            ("spring", "Przebudzenie lasu", "seasonal", datetime(year, 3, 20, tzinfo=zone), datetime(year, 3, 28, tzinfo=zone), 100, 130, 1),
            ("harvest", "Święto Plonów", "holiday", datetime(year,9,22,tzinfo=zone), datetime(year,9,29,tzinfo=zone),120,115,0),
            ("solstice", "Noc Tysiąca Ognisk", "holiday", datetime(year,6,20,tzinfo=zone), datetime(year,6,25,tzinfo=zone),110,120,0),
            ("balance", "Dni Równowagi", "holiday", datetime(year,3,20,tzinfo=zone), datetime(year,3,23,tzinfo=zone),115,120,0),
        ):
            WorldEvent.objects.get_or_create(key=prefix+f"{key}-{year}", defaults=dict(name=name, kind=kind, starts_at=start, ends_at=end, ore_percent=ore, experience_percent=experience, premium_bonus=premium, description="Premie do nagród za polowania, wydobycie i wyprawy. Odłamki bonusowe dotyczą wypraw czasowych."))
    seasonal_names = (
        "Szlaki pod szronem", "Warty przy zimowych ogniskach", "Roztopy na trakcie",
        "Wiosenne zbiory ziół", "Przeprawy przez wezbrane strumienie", "Letnie karawany",
        "Długie patrole lata", "Zbiory na polach ryżowych", "Jesienne transporty rudy",
        "Zapasy przed chłodem", "Mgły nad doliną", "Pierwsze zimowe warty",
    )
    for year in (now.year-1, now.year, now.year+1):
        for month, name in enumerate(seasonal_names, 1):
            WorldEvent.objects.get_or_create(key=prefix+f"season-window-{year}-{month}",defaults=dict(
                name=name,kind="seasonal",starts_at=datetime(year,month,5,tzinfo=zone),ends_at=datetime(year,month,9,tzinfo=zone),
                ore_percent=115 if month%2 else 110,experience_percent=110 if month%2 else 115,
                description="Sezonowe prace mieszkańców. Premie nie sumują się: obowiązuje najwyższa dla danego zasobu. Wszystkie szlaki pozostają dostępne."))
    # A deterministic daily draw survives restarts and concurrent initialization.
    day = now.date()
    draw = int(hashlib.sha256(("ore-empire-events-v1:" + day.isoformat()).encode()).hexdigest()[:8], 16)
    if draw % 4 == 0:
        start = datetime(day.year, day.month, day.day, draw % 20, tzinfo=zone)
        WorldEvent.objects.get_or_create(key=prefix+"random-" + day.isoformat(), defaults=dict(name="Szczęśliwa żyła rudy", kind="random", starts_at=start, ends_at=start.astimezone(dt_timezone.utc) + timedelta(hours=4), ore_percent=150, experience_percent=100, description="Kopacze odkryli bogate złoże. Przez cztery godziny nagrody w rudzie są większe."))


from django.db import transaction
@transaction.atomic
def ensure_world_events(now=None):
    from .models import World,EventSchedule
    from .worlds import current_world
    from .world_releases import sync_releases
    from .barrier import region_ids
    from .regional_events import seed_regional,VERSION
    now=(now or timezone.now()).astimezone(POLISH_TIME)
    world=World.objects.select_for_update().get(pk=current_world().pk)
    flags=sync_releases(world,now)
    ids=region_ids(world)
    cursor,_=EventSchedule.objects.get_or_create(world=world)
    stamp=f"v{VERSION}:{now.date()}:{','.join(map(str,sorted(ids)))}:{','.join(sorted(flags))}"
    marker=('' if world.pk==1 else f'world-{world.pk}-')+f'season-window-{now.year}-{now.month}'
    if cursor.stamp==stamp and WorldEvent.objects.filter(key=marker).exists():return
    _seed_legacy(now)
    if len(ids)==1 or world.is_current:
        if len(ids)>1:WorldEvent.objects.filter(world_id__in=ids,key__startswith='regional-v1-').exclude(world=world).exclude(region='').update(enabled=False)
        seed_regional(world,flags,now)
    cursor.stamp=stamp;cursor.save(update_fields=['stamp'])
