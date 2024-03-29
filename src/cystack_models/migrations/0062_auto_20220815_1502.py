# Generated by Django 3.1.4 on 2022-08-15 15:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0061_event_metadata'),
    ]

    operations = [
        migrations.CreateModel(
            name='RelaySubdomain',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subdomain', models.CharField(db_index=True, max_length=128)),
                ('created_time', models.FloatField()),
                ('is_deleted', models.BooleanField(default=False)),
                ('domain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relay_subdomains', to='cystack_models.relaydomain')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relay_subdomains', to='cystack_models.user')),
            ],
            options={
                'db_table': 'cs_relay_subdomains',
                'unique_together': {('subdomain', 'domain')},
            },
        ),
        migrations.AddField(
            model_name='relayaddress',
            name='subdomain',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='relay_addresses', to='cystack_models.relaysubdomain'),
        ),
    ]
