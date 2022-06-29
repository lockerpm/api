from django.db import models


class Ownership(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    description = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        db_table = 'cs_ownership'
