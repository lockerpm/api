# Generated by Django 3.1.4 on 2022-07-21 04:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0052_domain_domainownership_enterprise_enterprisegroup_enterprisegroupmember_enterprisemember_enterprisem'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnterpriseRolePermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enterprise_role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enterprise_role_permissions', to='cystack_models.enterprisememberrole')),
                ('permission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enterprise_role_permissions', to='cystack_models.permission')),
            ],
            options={
                'db_table': 'e_role_permissions',
                'unique_together': {('enterprise_role', 'permission')},
            },
        ),
    ]