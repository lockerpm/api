# Generated by Django 3.2.16 on 2022-12-20 05:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0086_auto_20221206_1803'),
    ]

    operations = [
        migrations.AddField(
            model_name='cipher',
            name='last_use_date',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='cipher',
            name='num_use',
            field=models.IntegerField(default=0),
        ),
    ]