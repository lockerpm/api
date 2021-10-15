from django.db import models

from cystack_models.models.members.team_members import TeamMember
from cystack_models.models.teams.groups import Group


class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="groups_members")
    member = models.ForeignKey(TeamMember, on_delete=models.CASCADE, related_name="groups_members")

    class Meta:
        db_table = 'cs_groups_members'
        unique_together = ('group', 'member')

    @classmethod
    def create_multiple(cls, group: Group, *member_ids):
        group_members = []
        for member_id in member_ids:
            group_members.append(cls(group=group, member_id=member_id))
        cls.objects.bulk_create(group_members, ignore_conflicts=True)
