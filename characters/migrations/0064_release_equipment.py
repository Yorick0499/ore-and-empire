from django.db import migrations

from characters.release_equipment_v1 import seed


def add_release_equipment(apps, schema_editor):
    blueprints = apps.get_model('characters', 'ItemBluePrint').objects.using(schema_editor.connection.alias)
    seed(blueprints)


class Migration(migrations.Migration):
    dependencies = [('characters', '0063_patrol_rank_permits')]
    operations = [migrations.RunPython(add_release_equipment, migrations.RunPython.noop)]
