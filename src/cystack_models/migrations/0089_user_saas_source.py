# Generated by Django 3.2.18 on 2023-03-03 07:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0088_promocode_is_saas_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='saas_source',
            field=models.CharField(default=None, max_length=32, null=True),
        ),
    ]
