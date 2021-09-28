from django.db import models

from cystack_models.models.members.team_members import TeamMember
from cystack_models.models.teams.groups import Group


class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="groups_members")
    member = models.ForeignKey(TeamMember, on_delete=models.CASCADE, related_name="groups_members")

    class Meta:
        db_table = 'cs_groups_members'
        unique_together = ('group', 'member')
