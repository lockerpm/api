# Generated by Django 3.1.4 on 2022-06-29 02:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0042_auto_20220525_0929'),
    ]

    operations = [
        migrations.AddField(
            model_name='userscore',
            name='cipher5',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='userscore',
            name='cipher6',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='userscore',
            name='cipher7',
            field=models.FloatField(default=0),
        ),
    ]