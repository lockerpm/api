from django.db import models


class SSOProviderORM(models.Model):
    id = models.CharField(primary_key=True, max_length=128)
    name = models.CharField(max_length=128)
    order_index = models.IntegerField(db_index=True)

    class Meta:
        db_table = 'cs_sso_providers'
