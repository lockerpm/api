# Generated by Django 3.1.4 on 2022-08-11 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0058_enterprisepolicy_policyfailedlogin_policymasterpassword_policypassword_policypasswordless'),
    ]

    operations = [
        migrations.AddField(
            model_name='enterprisemember',
            name='is_activated',
            field=models.BooleanField(default=True),
        ),
    ]
