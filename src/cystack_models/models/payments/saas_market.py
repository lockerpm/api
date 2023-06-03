from django.db import models


class SaasMarket(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, unique=True)
    lifetime_duration = models.PositiveIntegerField(null=True, default=None)

    class Meta:
        db_table = 'cs_saas_markets'
