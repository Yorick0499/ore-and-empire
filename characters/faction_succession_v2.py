"""Keep the Brotherhood together when its doctrine changes after the Barrier."""
from . import faction_succession_v1

BELIAR = 'VEIL_ORDER'
FORMER_SCHOOL_RUNES = (
    'firebolt', 'fireball', 'firerain', 'thunderbolt', 'icecube', 'icewave',
)
FORMER_EXPEDITION_RUNES = (
    'oe-nk-nk_firerain-rune', 'oe-nk-nk_thunderstorm-rune',
    'oe-nk-adanos_depths-rune', 'oe-nk-innos_beacon-rune',
)


def destination(camp, rank):
    if camp == 'SWAMP_CAMP':
        return BELIAR
    return faction_succession_v1.destination(camp, rank)


def reform(apps, succession, using='default'):
    Guild = apps.get_model('characters', 'CampGuild')
    Membership = apps.get_model('characters', 'FactionMembership')
    Quest = apps.get_model('characters', 'CampQuest')

    # Reuse the guild row so raids, contributions and the remaining treasury
    # retain their identities. Historical transfers to other guilds stand.
    guild = Guild.objects.using(using).filter(world_id=succession.race.colony_id, camp='SWAMP_CAMP').first()
    if guild is None:
        return
    guild.camp = BELIAR
    guild.save(using=using, update_fields=['camp'])
    members = Membership.objects.using(using).filter(succession=succession, historical_camp='SWAMP_CAMP')
    member_ids = list(members.values_list('profile_id', flat=True))
    quests = Quest.objects.using(using).filter(profile_id__in=member_ids, promoted_at__isnull=True, rank_key__startswith='ADV_')
    for quest in quests.iterator():
        tier = quest.rank_key.rsplit('_', 1)[-1]
        if tier not in {'4', '5', '6', '7'}:
            continue
        key = f'ADV_{BELIAR}_{tier}'
        if not Quest.objects.using(using).filter(profile_id=quest.profile_id, rank_key=key).exists():
            Quest.objects.using(using).filter(pk=quest.pk).update(rank_key=key)
    Profile = apps.get_model('characters', 'PlayerProfile')
    from django.db.models import Q
    retired = Q(prepared_magic__blueprint__catalog_key__in=[
        *FORMER_EXPEDITION_RUNES,
        *(f'{game}-itarrune{key}' for game in ('g1', 'g2') for key in FORMER_SCHOOL_RUNES),
    ])
    retired |= Q(prepared_magic__blueprint__catalog_key__startswith='oe-fire-')
    retired |= Q(prepared_magic__blueprint__catalog_key__startswith='oe-water-')
    Profile.objects.using(using).filter(pk__in=member_ids).filter(retired).update(prepared_magic=None)
    members.update(faction=BELIAR, guild=guild)


def apply(apps, race, using='default'):
    succession = faction_succession_v1.apply(apps, race, using)
    reform(apps, succession, using)
    return succession
