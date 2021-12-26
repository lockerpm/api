# Generated by Django 3.1.4 on 2021-12-24 04:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0021_useraccesstoken_sso_token_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.FloatField()),
                ('refresh_token', models.CharField(max_length=255)),
                ('token_type', models.CharField(max_length=128)),
                ('scope', models.CharField(max_length=255)),
                ('client_id', models.CharField(max_length=128)),
                ('device_name', models.CharField(max_length=128, null=True)),
                ('device_type', models.IntegerField(null=True)),
                ('device_identifier', models.CharField(max_length=128)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_devices', to='cystack_models.user')),
            ],
            options={
                'db_table': 'cs_devices',
                'unique_together': {('device_identifier', 'user')},
            },
        ),
        migrations.CreateModel(
            name='DeviceAccessToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.TextField()),
                ('expired_time', models.FloatField()),
                ('grant_type', models.CharField(blank=True, default='', max_length=128, null=True)),
                ('sso_token_id', models.CharField(default=None, max_length=128, null=True)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='device_access_tokens', to='cystack_models.device')),
            ],
            options={
                'db_table': 'cs_device_access_tokens',
            },
        ),
    ]
