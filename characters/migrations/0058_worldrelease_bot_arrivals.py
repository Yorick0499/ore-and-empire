from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('characters', '0057_expedition_runes')]
    operations = [
        migrations.AddField(
            model_name='worldrelease',
            name='bot_arrivals',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
