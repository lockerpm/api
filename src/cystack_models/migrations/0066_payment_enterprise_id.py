# Generated by Django 3.1.4 on 2022-08-23 06:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0065_auto_20220822_1213'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='enterprise_id',
            field=models.CharField(default=None, max_length=128, null=True),
        ),
    ]