import uuid

from django.db import models


class AbstractTeamORM(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    name = models.CharField(max_length=128, blank=True, default="My Team")
    description = models.CharField(max_length=255, blank=True, default="")
    creation_date = models.FloatField(null=True)
    revision_date = models.FloatField(null=True)
    locked = models.BooleanField(default=False)
    business_name = models.CharField(max_length=128, blank=True, default="")
    key = models.CharField(max_length=512, null=True)
    default_collection_name = models.CharField(max_length=512, null=True)
    public_key = models.TextField(null=True)
    private_key = models.TextField(null=True)
    personal_share = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @classmethod
    def create(cls, **data):
        raise NotImplementedError

    def lock_pm_team(self, lock: bool):
        self.locked = lock
        self.save()
