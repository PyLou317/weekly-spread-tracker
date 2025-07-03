
# Generated migration

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='candidate',
            old_name='candidate_name',
            new_name='contractor_name',
        ),
    ]
