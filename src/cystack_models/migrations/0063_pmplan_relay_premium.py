# Generated by Django 3.1.4 on 2022-08-15 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0062_auto_20220815_1502'),
    ]

    operations = [
        migrations.AddField(
            model_name='pmplan',
            name='relay_premium',
            field=models.BooleanField(default=False),
        ),
    ]