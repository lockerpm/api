import uuid

from django.db import models

from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.users.users import User
from cystack_models.models.members.team_members import TeamMember
from shared.constants.members import MEMBER_ROLE_OWNER
from shared.utils.app import now


class EnterpriseGroup(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    name = models.CharField(max_length=128)
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="created_enterprise_groups", null=True)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="groups")

    class Meta:
        db_table = 'e_enterprise_groups'

    @classmethod
    def create(cls, enterprise: Enterprise, name: str, created_by=None):
        new_group = cls(
            name=name, enterprise=enterprise, creation_date=now(), revision_date=now(),
            created_by=created_by
        )
        new_group.save()
        return new_group

    @classmethod
    def get_list_user_group_ids(cls, user):
        return list(
            cls.objects.filter(enterprise__enterprise_members__user=user).values_list('id', flat=True)
        )

    @classmethod
    def get_list_active_user_group_ids(cls, user):
        return list(
            cls.objects.filter(
                enterprise__locked=False,
                enterprise__enterprise_members__user=user,
                enterprise__enterprise_members__is_activated=True
            ).values_list('id', flat=True)
        )

    def full_delete(self):
        # Delete sharing group members
        sharing_group_members = self.sharing_groups.values_list('groups_members__member_id', flat=True)
        TeamMember.objects.filter(
            id__in=list(sharing_group_members), is_added_by_group=True
        ).exclude(role_id=MEMBER_ROLE_OWNER).delete()
        # Delete this group objects
        self.delete()
