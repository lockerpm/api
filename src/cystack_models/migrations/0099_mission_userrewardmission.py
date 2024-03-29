# Generated by Django 3.2.18 on 2023-04-25 07:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0098_release_environment'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mission',
            fields=[
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=128)),
                ('description_en', models.CharField(blank=True, default='', max_length=255)),
                ('description_vi', models.CharField(blank=True, default='', max_length=255)),
                ('created_time', models.IntegerField()),
                ('mission_type', models.CharField(max_length=64)),
                ('order_index', models.IntegerField()),
                ('extra_requirements', models.CharField(blank=True, default=None, max_length=255, null=True)),
            ],
            options={
                'db_table': 'cs_missions',
                'ordering': ['-order_index'],
            },
        ),
        migrations.CreateModel(
            name='UserRewardMission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(default='not_started', max_length=64)),
                ('is_claimed', models.BooleanField(default=False)),
                ('completed_time', models.IntegerField(null=True)),
                ('mission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_reward_missions', to='cystack_models.mission')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_reward_missions', to='cystack_models.user')),
            ],
            options={
                'db_table': 'cs_user_reward_missions',
                'unique_together': {('user', 'mission')},
            },
        ),
    ]
