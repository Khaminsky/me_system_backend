# Generated migration for adding project field to Indicator model

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indicators', '0002_indicator_filter_criteria'),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='indicator',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='indicators', to='projects.project'),
        ),
    ]

