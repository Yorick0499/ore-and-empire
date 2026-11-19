"""Bounded arrivals when a named server milestone is reached."""
from collections import Counter

from django.contrib.auth.models import User
from django.db.models import Count
from uuid import uuid4

from .barrier import region_ids
from .bot_personalities import assignment
from .models import PlayerProfile, WorldRelease
from .realms import open_worlds, world_scope
from .world_releases import RELEASES

MILESTONE_KEYS = tuple(key for key, *_ in RELEASES if key != 'foundations')
ARRIVALS_PER_MILESTONE = 5
AUTOMATIC_POPULATION_CAP = 280


def base_bot_target(world):
    arrivals = PlayerProfile.objects.filter(world=world, is_bot=True, user__username__startswith='arrival-').count()
    return max(0, world.bot_count - arrivals)


def admit_next_cohort(primary):
    """Call under the primary worker's lease. Existing manual limits take precedence."""
    ids = region_ids(primary.world_id)
    if len(ids) < 2:
        return
    pending = dict(WorldRelease.objects.filter(
        world_id=primary.world_id, key__in=MILESTONE_KEYS, bot_arrivals__isnull=True,
    ).values_list('key', 'pk'))
    release_id = next((pending[key] for key in MILESTONE_KEYS if key in pending), None)
    if release_id is None:
        return
    with primary.work():
        release = WorldRelease.objects.select_for_update().get(pk=release_id)
        if release.bot_arrivals is not None:
            return
        worlds = list(open_worlds().select_for_update().filter(pk__in=ids, configured=True).order_by('pk'))
        capacity = min(ARRIVALS_PER_MILESTONE, AUTOMATIC_POPULATION_CAP - sum(w.bot_count for w in worlds))
        population = dict(PlayerProfile.objects.filter(world_id__in=ids, is_bot=True, user__is_active=True)
                          .values('world_id').annotate(total=Count('pk')).values_list('world_id', 'total'))
        eligible = [w for w in worlds if w.bot_count and population.get(w.pk) == w.bot_count]
        planned = Counter()
        for n in range(max(0, capacity)):
            if not eligible:
                break
            world = min(eligible, key=lambda w: (w.bot_count + planned[w.pk], w.pk))
            with world_scope(world):
                user = User.objects.create_user(f'arrival-{release.key}-{uuid4().hex}', password=None)
                profile = user.characters.get(world=world)
                profile.is_bot = True
                profile.bot_role = ('hunter', 'trader', 'miner')[(release.pk + n) % 3]
                profile.bot_personality, profile.bot_session_shift = assignment(profile.pk, world.pk)
                profile.save(update_fields=['is_bot', 'bot_role', 'bot_personality', 'bot_session_shift'])
            planned[world.pk] += 1
        for world in eligible:
            if planned[world.pk]:
                world.bot_count += planned[world.pk]
                world.save(update_fields=['bot_count'])
        release.bot_arrivals = sum(planned.values())
        release.save(update_fields=['bot_arrivals'])
