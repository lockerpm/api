from django.db import models


class RelayDomain(models.Model):
    id = models.CharField(primary_key=True, max_length=64)

    class Meta:
        db_table = 'cs_relay_domains'
