"""Supply existing recipes through the hunts used in the Khorinis campaign."""


def seed_campaign_hunting_materials(blueprints, tables):
    for creature, material, weight in (
        ('k2_goblin', 'craft-herbs', 3200),
        ('k2_field_raider', 'craft-steel', 1800),
    ):
        blueprint = blueprints.filter(catalog_key=material).values_list('pk', flat=True).first()
        if blueprint is not None:
            tables.get_or_create(
                key=creature,
                defaults={'entries': [{'blueprint': blueprint, 'weight': weight}]},
            )
