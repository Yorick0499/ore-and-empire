"""Availability checks shared by merchants, equipment, magic and barter."""

from .release_equipment_v1 import DELIVERIES, definitions

GEAR = {key: (release, band) for release, band, key, _, _ in definitions()}
RUNES = {key: rune for _, _, key, _, rune in definitions() if rune}
RELEASE_TITLES = {delivery.release: delivery.title for delivery in DELIVERIES}
PORTAL_RELEASES = frozenset(RELEASE_TITLES) - {'barrier'}


def published(world_id):
    from django.utils import timezone
    from .barrier import region_ids
    from .models import WorldRelease
    from .realms import _union_cache

    cache = _union_cache.get()
    cache_key = ('release-equipment', world_id)
    if cache is not None and cache_key in cache:
        return cache[cache_key]
    regions = region_ids(world_id)
    keys = frozenset()
    if len(regions) > 1:
        keys = frozenset(WorldRelease.objects.filter(
            world_id__in=regions, key__in=RELEASE_TITLES, released_at__lte=timezone.now(),
        ).values_list('key', flat=True))
    if cache is not None:
        for region in regions:
            cache[('release-equipment', region)] = keys
    return keys


def release_title(blueprint):
    rule = GEAR.get(blueprint.catalog_key)
    return RELEASE_TITLES[rule[0]] if rule else ''


def trade_allowed(world_id, blueprint):
    rule = GEAR.get(blueprint.catalog_key)
    return not rule or rule[0] in published(world_id)


def requirement(profile, blueprint):
    rule = GEAR.get(blueprint.catalog_key)
    if not rule:
        return ''
    release, band = rule
    if not trade_allowed(profile.world_id, blueprint):
        return f'Wymagana odsłona świata: {RELEASE_TITLES[release]}.'
    if band == 2 and release in PORTAL_RELEASES:
        from .jarkendar import unlocked

        if not unlocked(profile):
            return 'Najpierw odbierz zadanie Droga za portal.'
    return ''


def filter_stock(world_id, queryset, *, portal=True, field='catalog_key'):
    keys = published(world_id)
    locked = [key for key, (release, band) in GEAR.items()
              if release not in keys or (not portal and band == 2 and release in PORTAL_RELEASES)]
    return queryset.exclude(**{f'{field}__in': locked}) if locked else queryset
