# Generated by Django 3.1.4 on 2022-07-21 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0053_enterpriserolepermission'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='brand',
            field=models.CharField(blank=True, default='', max_length=32, null=True),
        ),
    ]