# Generated by Django 3.2.18 on 2023-03-23 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0094_quickshare_each_email_access_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quickshare',
            name='require_otp',
            field=models.BooleanField(default=True),
        ),
    ]