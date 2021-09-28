import uuid

from django.db import models

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
