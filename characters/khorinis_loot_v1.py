"""Seed missing local hunting materials without replacing operator loot tables."""


def seed_hunting_materials(blueprints, tables):
    for creature, material in (("k2_scavenger", "raw-meat"), ("k2_wolf", "wolf-skin")):
        blueprint = blueprints.filter(catalog_key=material).values_list("pk", flat=True).first()
        if blueprint is not None:
            tables.get_or_create(
                key=creature,
                defaults={"entries": [{"blueprint": blueprint, "weight": 6000}]},
            )
