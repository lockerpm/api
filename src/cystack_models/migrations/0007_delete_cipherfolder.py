# Generated by Django 3.1.4 on 2021-10-07 11:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0006_user_internal_id'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CipherFolder',
        ),
    ]