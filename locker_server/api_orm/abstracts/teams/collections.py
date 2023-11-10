import uuid

from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.utils.app import now


class AbstractCollectionORM(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    name = models.TextField()
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    external_id = models.CharField(max_length=300, null=True)
    is_default = models.BooleanField(default=False)
    team = models.ForeignKey(locker_server_settings.LS_TEAM_MODEL, on_delete=models.CASCADE, related_name="collections")

    class Meta:
        abstract = True

    @classmethod
    def create(cls, team, **data):
        new_collection = cls(
            team=team,
            name=data.get("name"),
            creation_date=data.get("creation_date", now()),
            revision_date=data.get("revision_date", now()),
            external_id=data.get("external_id", None),
            is_default=data.get("is_default", False)
        )
        new_collection.save()
        return new_collection
