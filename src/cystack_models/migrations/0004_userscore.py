# Generated by Django 3.1.4 on 2021-09-30 08:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0003_auto_20210930_1500'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserScore',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='user_score', serialize=False, to='cystack_models.user')),
                ('cipher0', models.FloatField(default=0)),
                ('cipher1', models.FloatField(default=0)),
                ('cipher2', models.FloatField(default=0)),
                ('cipher3', models.FloatField(default=0)),
                ('cipher4', models.FloatField(default=0)),
            ],
            options={
                'db_table': 'cs_user_score',
            },
        ),
    ]