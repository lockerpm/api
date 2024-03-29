# Generated by Django 3.2.18 on 2023-06-02 10:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0106_promocode_only_period'),
    ]

    operations = [
        migrations.CreateModel(
            name='SaasMarket',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('lifetime_duration', models.PositiveIntegerField(default=None, null=True)),
            ],
            options={
                'db_table': 'cs_saas_markets',
            },
        ),
        migrations.AddField(
            model_name='promocode',
            name='saas_plan',
            field=models.CharField(default=None, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='promocode',
            name='saas_market',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='promo_codes', to='cystack_models.saasmarket'),
        ),
    ]
