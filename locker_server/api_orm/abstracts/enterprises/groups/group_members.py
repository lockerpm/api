from django.db import models

from locker_server.settings import locker_server_settings


class AbstractEnterpriseGroupMemberORM(models.Model):
    group = models.ForeignKey(
        locker_server_settings.LS_ENTERPRISE_GROUP_MODEL, on_delete=models.CASCADE, related_name="group_members"
    )
    member = models.ForeignKey(
        locker_server_settings.LS_ENTERPRISE_MEMBER_MODEL, on_delete=models.CASCADE, related_name="groups_members"
    )

    class Meta:
        abstract = True
        unique_together = ('group', 'member')

    @classmethod
    def create_multiple(cls, datas):
        raise NotImplementedError

    @classmethod
    def create_multiple_by_member(cls, member, *group_ids):
        member_groups = []
        for group_id in group_ids:
            member_groups.append(cls(group_id=group_id, member=member))
        cls.objects.bulk_create(member_groups, ignore_conflicts=True, batch_size=10)

    # @classmethod
    # def remove_multiple_by_member_ids(cls, group, deleted_member_ids):
    #     # Remove member in sharing teams
    #     deleted_groups_members = group.groups_members.filter(member_id__in=deleted_member_ids)
    #     sharing_group_members = group.sharing_groups.filter(
    #         groups_members__member__user_id__in=deleted_groups_members.values_list('member__user_id', flat=True)
    #     ).values_list('groups_members__member_id', flat=True)
    #     TeamMember.objects.filter(
    #         id__in=list(sharing_group_members), is_added_by_group=True
    #     ).exclude(role_id=MEMBER_ROLE_OWNER).delete()
    #     # Remove enterprise group members
    #     deleted_groups_members.delete()
