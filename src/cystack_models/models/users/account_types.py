from django.db import models


class AccountType(models.Model):
    name = models.CharField(primary_key=True, max_length=128)

    class Meta:
        db_table = 'cs_account_types'
        managed = False
