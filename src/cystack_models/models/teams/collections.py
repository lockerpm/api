import uuid

from django.db import models

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
