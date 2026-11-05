from django.db import migrations


def update_narrative(apps,schema_editor):
    from characters.story_narrative import apply_narrative
    apply_narrative(apps,schema_editor.connection.alias)


class Migration(migrations.Migration):
    dependencies=[('characters','0022_campraid_campraidreward_campraidstrike_and_more')]
    operations=[migrations.RunPython(update_narrative,migrations.RunPython.noop)]
