# Generated by Django 5.2.1 on 2025-07-08 05:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contractors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='contractor_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
