from django.db import migrations

from characters.rune_catalog_v1 import rename_water_runes, seed_expeditions


def install_runes(apps, schema_editor):
    alias = schema_editor.connection.alias
    blueprints = apps.get_model('characters', 'ItemBluePrint').objects.using(alias)
    rename_water_runes(blueprints)
    worlds = apps.get_model('characters', 'World').objects.using(alias)
    if worlds.filter(universe='GOTHIC_II', is_open=True, status='active').exists():
        seed_expeditions(blueprints)


class Migration(migrations.Migration):
    dependencies = [('characters', '0056_khorinis_hunting_materials')]
    operations = [migrations.RunPython(install_runes, migrations.RunPython.noop)]
