from django.db import models

from locker_server.settings import locker_server_settings


class AbstractGroupMemberORM(models.Model):
    group = models.ForeignKey(
        locker_server_settings.LS_GROUP_MODEL, on_delete=models.CASCADE, related_name="groups_members"
    )
    member = models.ForeignKey(
        locker_server_settings.LS_TEAM_MEMBER_MODEL, on_delete=models.CASCADE, related_name="groups_members"
    )

    class Meta:
        abstract = True
        unique_together = ('group', 'member')

    @classmethod
    def create_multiple(cls, group, *member_ids):
        group_members = []
        for member_id in member_ids:
            group_members.append(cls(group=group, member_id=member_id))
        cls.objects.bulk_create(group_members, ignore_conflicts=True)

    @classmethod
    def create_multiple_by_member(cls, member, *group_ids):
        member_groups = []
        for group_id in group_ids:
            member_groups.append(cls(group_id=group_id, member=member))
        cls.objects.bulk_create(member_groups, ignore_conflicts=True, batch_size=10)

    @classmethod
    def retrieve_or_create(cls, group_id, member_id):
        group_member, is_created = cls.objects.get_or_create(
            group_id=group_id, member_id=member_id, defaults={
                "group_id": group_id, "member_id": member_id
            }
        )
        return group_member
