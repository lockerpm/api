from django.db import models

from cystack_models.models.enterprises.members.enterprise_members import EnterpriseMember
from cystack_models.models.enterprises.groups.groups import EnterpriseGroup


class EnterpriseGroupMember(models.Model):
    group = models.ForeignKey(EnterpriseGroup, on_delete=models.CASCADE, related_name="groups_members")
    member = models.ForeignKey(EnterpriseMember, on_delete=models.CASCADE, related_name="groups_members")

    class Meta:
        db_table = 'e_groups_members'
        unique_together = ('group', 'member')

    @classmethod
    def create_multiple(cls, group: EnterpriseGroup, *member_ids):
        group_members = []
        for member_id in member_ids:
            group_members.append(cls(group=group, member_id=member_id))
        cls.objects.bulk_create(group_members, ignore_conflicts=True)

    @classmethod
    def create_multiple_by_member(cls, member: EnterpriseMember, *group_ids):
        member_groups = []
        for group_id in group_ids:
            member_groups.append(cls(group_id=group_id, member=member))
        cls.objects.bulk_create(member_groups, ignore_conflicts=True, batch_size=10)
