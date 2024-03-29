# Generated by Django 3.1.4 on 2022-11-23 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserStatistic',
            fields=[
                ('user_id', models.IntegerField(primary_key=True, serialize=False)),
                ('country', models.CharField(max_length=32)),
                ('verified', models.BooleanField(default=True)),
                ('created_master_password', models.BooleanField(default=False)),
                ('cs_created_date', models.DateTimeField()),
                ('lk_created_date', models.DateTimeField(null=True)),
                ('use_web_app', models.BooleanField(default=False)),
                ('use_android', models.BooleanField(default=False)),
                ('use_ios', models.BooleanField(default=False)),
                ('use_extension', models.BooleanField(default=False)),
                ('use_desktop', models.BooleanField(default=False)),
                ('total_items', models.IntegerField(default=0)),
                ('num_password_items', models.IntegerField(default=0)),
                ('num_note_items', models.IntegerField(default=0)),
                ('num_card_items', models.IntegerField(default=0)),
                ('num_identity_items', models.IntegerField(default=0)),
                ('num_crypto_backup_items', models.IntegerField(default=0)),
                ('num_totp_items', models.IntegerField(default=0)),
                ('num_private_emails', models.IntegerField(default=0)),
                ('deleted_account', models.BooleanField(default=False)),
                ('lk_plan', models.CharField(default='pm_free', max_length=64)),
                ('utm_source', models.CharField(blank=True, default=None, max_length=64, null=True)),
                ('paid_money', models.FloatField(default=0)),
            ],
            options={
                'db_table': 'lk_user_statistics',
            },
        ),
    ]
