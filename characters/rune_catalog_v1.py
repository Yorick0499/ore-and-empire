"""Stable default identities for the school runes and the joined-world upgrades."""

WATER_NAMES = {
    'waterlance': ('Lodowa lanca', 'Ostrze Adanosa'),
    'thunderball': ('Piorun kulisty', 'Rozbłysk Adanosa'),
    'chainlightning': ('Grom', 'Wyrok Adanosa'),
}

EXPEDITIONS = (
    ('barrier_echo', 'Pieczęć Śniącego', 'brotherhood', 1, 18, 255, 'magic', 0, 2, 'item_g1_itarrunepyrokinesis'),
    ('adanos_depths', 'Głębia Adanosa', 'water', 2, 20, 350, 'magic', 50, 0, 'item_g1_itarruneicewave'),
    ('innos_beacon', 'Latarnia Innosa', 'fire', 2, 20, 370, 'fire', 25, 0, 'item_g1_itarrunefirerain'),
    ('sleeper_rift', 'Szczelina Śniącego', 'brotherhood', 2, 20, 340, 'magic', 0, 2, 'item_g1_itarrunepyrokinesis'),
)


def rename_water_runes(blueprints):
    for key, (previous, name) in WATER_NAMES.items():
        suffix = ' — runa Kręgu Wody'
        blueprints.filter(
            catalog_key__in=[f'oe-water-{region}-{key}-rune' for region in ('g1', 'g2')],
            name=previous + suffix,
        ).update(name=name + suffix)


def seed_expeditions(blueprints):
    for key, name, _, tier, *_combat, art in EXPEDITIONS:
        blueprints.get_or_create(catalog_key=f'oe-nk-{key}-rune', defaults={
            'name': name + ' — runa wyprawy', 'kind': 'rune', 'source_game': 'GOTHIC_II',
            'min_level': 35 if tier == 1 else 38, 'base_value': 2000 if tier == 1 else 3200,
            'merchant': True, 'art_key': art,
            'original_stats': {'runtime_supported': True, 'browser_gate': 'joined' if tier == 1 else 'jarkendar',
                               'balance': 'expedition-runes-v1'},
        })
