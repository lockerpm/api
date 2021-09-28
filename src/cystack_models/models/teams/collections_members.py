from django.db import models

from cystack_models.models.members.team_members import TeamMember
from cystack_models.models.teams.collections import Collection


class CollectionMember(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="collections_groups")
    member = models.ForeignKey(TeamMember, on_delete=models.CASCADE, related_name="collections_groups")
    read_only = models.BooleanField(default=False)
    hide_passwords = models.BooleanField(default=False)

    class Meta:
        db_table = 'cs_collections_members'
        unique_together = ('collection', 'member')
