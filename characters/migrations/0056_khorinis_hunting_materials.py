from django.db import migrations

from characters.khorinis_loot_v1 import seed_hunting_materials


def install_on_existing_island(apps, schema_editor):
    alias = schema_editor.connection.alias
    worlds = apps.get_model("characters", "World").objects.using(alias)
    if worlds.filter(universe="GOTHIC_II", is_open=True).exists():
        blueprints = apps.get_model("characters", "ItemBluePrint").objects.using(alias)
        tables = apps.get_model("characters", "LootTable").objects.using(alias)
        seed_hunting_materials(blueprints, tables)


class Migration(migrations.Migration):
    dependencies = [("characters", "0055_manual_camp_raids")]
    operations = [migrations.RunPython(install_on_existing_island, migrations.RunPython.noop)]
