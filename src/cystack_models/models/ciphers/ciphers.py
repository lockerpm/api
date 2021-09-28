import uuid

from django.db import models

from cystack_models.models.teams.teams import Team
from cystack_models.models.users.users import User


class Cipher(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    creation_date = models.FloatField()
    revision_date = models.FloatField()
    deleted_date = models.FloatField()
    reprompt = models.IntegerField(default=0)

    score = models.FloatField(default=0)
    type = models.IntegerField()
    data = models.TextField(blank=True, null=True)
    favorites = models.TextField(blank=True, null=True)
    folders = models.TextField(blank=True, null=True, default="")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ciphers", null=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="teams", null=True)

    class Meta:
        db_table = 'cs_ciphers'


