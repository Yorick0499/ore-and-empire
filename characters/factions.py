"""Post-Barrier social identity; native camp/rank remain campaign history."""
from .models import CampGuild, FactionMembership, FactionSuccession, PlayerProfile

FACTIONS = (
    ('CITY_WATCH', 'Miasto Khorinis — Zakon Paladynów'),
    ('FIRE_ORDER', 'Klasztor Magów Ognia'),
    ('WATER_CIRCLE', 'Krąg Magów Wody'),
    ('BANDITS', 'Bandyci — Jarkendar'),
    ('MERCENARIES', 'Najemnicy — Łowcy Smoków'),
)
RANK_NAMES = {
    'CITY_WATCH': ('Rekrut straży', 'Strażnik miejski', 'Sierżant straży', 'Dowódca straży', 'Kandydat Zakonu', 'Rycerz', 'Paladyn', 'Mistrz Zakonu'),
    'FIRE_ORDER': ('Nowicjusz Ognia', 'Adept Ognia', 'Mag Ognia Khorinis', 'Arcymag klasztoru', 'Mistrz Ognia', 'Strażnik Świętego Ognia', 'Mistrz Kręgu Ognia', 'Awatar Innosa'),
    'WATER_CIRCLE': ('Uczeń Wody', 'Adept Wody', 'Mag Wody', 'Arcymag Wody', 'Mistrz Wody', 'Strażnik Równowagi', 'Mistrz Kręgu Wody', 'Awatar Adanosa'),
    'BANDITS': ('Kopacz', 'Rzezimieszek', 'Bandyta', 'Watażka', 'Przywódca szajki', 'Dowódca bandytów', 'Herszt bandytów', 'Baron bandytów'),
    'MERCENARIES': ('Pomocnik', 'Rekrut', 'Najemnik', 'Kapitan Najemników', 'Łowca Smoków', 'Weteran Łowców Smoków', 'Dowódca Łowców Smoków', 'Mistrz Łowców Smoków'),
}


def membership(profile):
    try:return profile.faction_membership
    except FactionMembership.DoesNotExist:return None


def faction_name(profile):
    member=membership(profile)
    if member:
        return dict(FACTIONS).get(member.faction, 'Bractwo — oczekuje na wybór frakcji')
    return profile.get_camp_display()


def rank_name(profile):
    from .camp_progression import BY_RANK
    member=membership(profile);rank=BY_RANK.get(profile.guild)
    if not member or member.faction not in RANK_NAMES or not rank or rank.camp!=profile.camp:return None
    # Ordinal is independent of grandfathered privilege levels and alliance_rank.
    return RANK_NAMES[member.faction][rank.tier]


def enroll(profile):
    """Called inside the existing player transaction after choosing a native path."""
    from .faction_succession_v1 import destination
    from .barrier import region_ids
    succession=FactionSuccession.objects.filter(race__colony_id__in=region_ids(profile.world_id)).select_related('race').first()
    if not succession:return
    faction=destination(profile.camp,profile.guild)
    guild=CampGuild.objects.get(world_id=succession.race.khorinis_id if faction in {'CITY_WATCH','FIRE_ORDER'} else succession.race.colony_id,camp='SWAMP_CAMP' if faction=='PENDING' else faction) if faction else None
    if not faction:return
    member,created=FactionMembership.objects.get_or_create(profile=profile,defaults={'succession':succession,'faction':faction,'guild':guild,'historical_camp':profile.camp,'historical_rank':profile.guild})
    if not created and (member.faction!=faction or member.guild_id!=guild.pk):
        member.faction=faction;member.guild=guild;member.save(update_fields=['faction','guild'])
    profile.faction_membership=member
    profile.__dict__.pop('_camp_perks',None)


def recruitment_camps(profile):
    from .realms import camps
    from .barrier import joined
    choices=camps(profile.world)
    return tuple(c for c in choices if c!='SWAMP_CAMP') if joined(profile.world_id) else choices


def recruitment_choices(profile):
    from .barrier import joined
    native=dict(PlayerProfile.CAMP_LIST)
    if joined(profile.world_id):
        native.update({'OLD_CAMP':'Bandyci — dawna droga Starego Obozu','NEW_CAMP':'Najemnicy — dawna droga Nowego Obozu','ONAR_MERCS':'Najemnicy — droga Onara','CITY_WATCH':dict(FACTIONS)['CITY_WATCH'],'FIRE_ORDER':dict(FACTIONS)['FIRE_ORDER']})
    return [(key,native[key]) for key in recruitment_camps(profile)]
