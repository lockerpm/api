import uuid

from django.db import models

from shared.utils.app import now
from cystack_models.models.teams.teams import Team


class Collection(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    name = models.TextField()
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    external_id = models.CharField(max_length=300, null=True)
    is_default = models.BooleanField(default=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="collections")

    class Meta:
        db_table = 'cs_collections'

    @classmethod
    def create(cls, team: Team, **data):
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
