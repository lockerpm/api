# Generated by Django 3.1.4 on 2021-11-29 09:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0017_remove_cipher_view_password'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emergencyaccess',
            name='status',
            field=models.CharField(default='invited', max_length=128),
        ),
        migrations.AlterField(
            model_name='emergencyaccess',
            name='type',
            field=models.CharField(max_length=128),
        ),
    ]