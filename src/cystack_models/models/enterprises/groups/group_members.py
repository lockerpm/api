from django.db import models

from cystack_models.models.enterprises.members.enterprise_members import EnterpriseMember
from cystack_models.models.enterprises.groups.groups import EnterpriseGroup
from cystack_models.models.members.team_members import TeamMember
from shared.constants.members import MEMBER_ROLE_OWNER


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

    @classmethod
    def remove_multiple_by_member_ids(cls, group: EnterpriseGroup, deleted_member_ids):
        # Remove member in sharing teams
        deleted_groups_members = group.groups_members.filter(member_id__in=deleted_member_ids)
        sharing_group_members = group.sharing_groups.filter(
            groups_members__member__user_id__in=deleted_groups_members.values_list('member__user_id', flat=True)
        ).values_list('groups_members__member_id', flat=True)
        TeamMember.objects.filter(
            id__in=list(sharing_group_members), is_added_by_group=True
        ).exclude(role_id=MEMBER_ROLE_OWNER).delete()
        # Remove enterprise group members
        deleted_groups_members.delete()
