import uuid

from django.db import models

from shared.utils.app import now
from cystack_models.models.teams.teams import Team


class Group(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    access_all = models.BooleanField(default=False)
    external_id = models.CharField(max_length=300)
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    name = models.TextField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="groups")

    class Meta:
        db_table = 'cs_groups'

    @classmethod
    def create(cls, team: Team, name: str, access_all: bool, collections: list):
        new_group = cls(
            team=team, name=name, access_all=access_all,
            creation_date=now(), revision_date=now()
        )
        new_group.save()
        if access_all is False and collections:
            new_group.collections_groups.model.create_multiple_by_group(new_group, *collections)
        return new_group
