# Generated by Django 3.1.4 on 2022-05-25 02:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0041_pmuserplan_extra_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pmuserplan',
            name='default_payment_method',
            field=models.CharField(default='card', max_length=128),
        ),
    ]
