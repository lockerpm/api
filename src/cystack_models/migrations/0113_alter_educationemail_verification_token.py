# Generated by Django 3.2.20 on 2023-09-11 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0112_alter_educationemail_verification_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='educationemail',
            name='verification_token',
            field=models.CharField(max_length=512, null=True),
        ),
    ]