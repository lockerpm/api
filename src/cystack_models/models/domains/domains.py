from django.db import models

from cystack_models.models.teams.teams import Team


class Domain(models.Model):
    id = models.AutoField(primary_key=True)
    created_time = models.FloatField()
    updated_time = models.FloatField(null=True)
    address = models.CharField(max_length=128)
    verification = models.BooleanField(default=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="domains")

    class Meta:
        db_table = 'cs_domains'
