"""Idempotent event schedules. No rewards are granted by calendar reads."""
from datetime import datetime, timedelta, timezone as dt_timezone
import hashlib
from django.utils import timezone
from .models import WorldEvent


def active_events(now=None):
    now = now or timezone.now()
    return WorldEvent.objects.filter(enabled=True, starts_at__lte=now, ends_at__gt=now)


def reward_snapshot(ore, experience, premium=0):
    events = list(active_events())
    return (
        ore * max([100, *(event.ore_percent for event in events)]) // 100,
        experience * max([100, *(event.experience_percent for event in events)]) // 100,
        premium + max([0, *(event.premium_bonus for event in events)]) if premium else 0,
        [event.name for event in events],
    )


def ensure_world_events(now=None):
    now = now or timezone.now()
    utc = dt_timezone.utc
    for year in (now.year - 1, now.year, now.year + 1):
        for key, name, kind, start, end, ore, experience, premium in (
            ("miners", "Święto Kopaczy", "seasonal", datetime(year, 10, 25, tzinfo=utc), datetime(year, 11, 8, tzinfo=utc), 125, 110, 1),
            ("winter", "Zimowe ogniska kolonii", "holiday", datetime(year, 12, 20, tzinfo=utc), datetime(year + 1, 1, 6, tzinfo=utc), 110, 125, 1),
            ("spring", "Przebudzenie lasu", "seasonal", datetime(year, 3, 20, tzinfo=utc), datetime(year, 3, 28, tzinfo=utc), 100, 130, 1),
        ):
            WorldEvent.objects.get_or_create(key=f"{key}-{year}", defaults=dict(name=name, kind=kind, starts_at=start, ends_at=end, ore_percent=ore, experience_percent=experience, premium_bonus=premium, description="Premie do nagród za polowania, wydobycie i wyprawy. Odłamki bonusowe dotyczą wypraw czasowych."))
    # A deterministic daily draw survives restarts and concurrent initialization.
    day = now.date()
    draw = int(hashlib.sha256(("ore-empire-events-v1:" + day.isoformat()).encode()).hexdigest()[:8], 16)
    if draw % 4 == 0:
        start = datetime(day.year, day.month, day.day, draw % 20, tzinfo=utc)
        WorldEvent.objects.get_or_create(key="random-" + day.isoformat(), defaults=dict(name="Szczęśliwa żyła rudy", kind="random", starts_at=start, ends_at=start + timedelta(hours=4), ore_percent=150, experience_percent=100, description="Kopacze odkryli bogate złoże. Przez cztery godziny nagrody w rudzie są większe."))
