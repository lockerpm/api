# Generated by Django 3.2.18 on 2023-05-26 03:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0105_userrewardmission_answer'),
    ]

    operations = [
        migrations.AddField(
            model_name='promocode',
            name='only_period',
            field=models.CharField(default=None, max_length=128, null=True),
        ),
    ]