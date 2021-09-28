import uuid

from django.db import models


class Team(models.Model):
    id = models.CharField(primary_key=True, max_length=128)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True, default="")
    locked = models.BooleanField(default=False)
    business_name = models.CharField(max_length=128, blank=True, default="")
    key = models.CharField(max_length=512, null=True)
    default_collection_name = models.CharField(max_length=512, null=True)
    public_key = models.TextField(null=True)
    private_key = models.TextField(null=True)

    class Meta:
        db_table = 'cs_teams'
