# Generated by Django 3.1.4 on 2022-03-09 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cystack_models', '0038_payment_mobile_invoice_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pmuserplan',
            name='pm_mobile_subscription',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
