# Generated by Django 3.1.4 on 2022-08-30 09:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0067_auto_20220823_1527'),
    ]

    operations = [
        migrations.AddField(
            model_name='relayaddress',
            name='block_spam',
            field=models.BooleanField(default=False),
        ),
    ]