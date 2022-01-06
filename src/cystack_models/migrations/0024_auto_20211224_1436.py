# Generated by Django 3.1.4 on 2021-12-24 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0023_auto_20211224_1436'),
    ]

    operations = [
        migrations.AddField(
            model_name='pmplan',
            name='emergency_access',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='pmplan',
            name='limit_crypto_asset',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='pmplan',
            name='limit_identity',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='pmplan',
            name='limit_password',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='pmplan',
            name='limit_payment_card',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='pmplan',
            name='limit_secure_note',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='pmplan',
            name='sync_device',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='pmplan',
            name='team_activity_log',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='pmplan',
            name='team_dashboard',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='pmplan',
            name='team_policy',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='pmplan',
            name='team_prevent_password',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='pmplan',
            name='tools_data_breach',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='pmplan',
            name='tools_master_password_check',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='pmplan',
            name='tools_password_reuse',
            field=models.BooleanField(default=False),
        ),
    ]