# Generated by Django 3.1.4 on 2022-10-13 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0073_domain_is_notify_failed'),
    ]

    operations = [
        migrations.AddField(
            model_name='pmuserplan',
            name='enterprise_trial_applied',
            field=models.BooleanField(default=False),
        ),
    ]
