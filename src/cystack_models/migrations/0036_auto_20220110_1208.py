# Generated by Django 3.1.4 on 2022-01-10 05:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0035_auto_20220110_1010'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userrefreshtoken',
            name='user',
        ),
        migrations.DeleteModel(
            name='UserAccessToken',
        ),
        migrations.DeleteModel(
            name='UserRefreshToken',
        ),
    ]
