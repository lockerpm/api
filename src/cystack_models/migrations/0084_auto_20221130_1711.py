# Generated by Django 3.1.4 on 2022-11-30 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0083_policy2fa'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enterprisemember',
            name='status',
            field=models.CharField(default='invited', max_length=128),
        ),
        migrations.AlterField(
            model_name='user',
            name='onboarding_process',
            field=models.TextField(blank=True, default={'enterprise_onboarding': [], 'tutorial': False, 'vault_to_dashboard': False, 'welcome': False}, max_length=512),
        ),
    ]
