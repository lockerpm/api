# Generated by Django 3.1.4 on 2022-07-21 02:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0050_pmuserplan_extra_plan'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='domainownership',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='domainownership',
            name='domain',
        ),
        migrations.RemoveField(
            model_name='domainownership',
            name='ownership',
        ),
        migrations.DeleteModel(
            name='Domain',
        ),
        migrations.DeleteModel(
            name='DomainOwnership',
        ),
        migrations.DeleteModel(
            name='Ownership',
        ),
    ]
