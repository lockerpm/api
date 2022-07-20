import uuid
from typing import Dict

from django.db import models

from shared.utils.app import now
from shared.constants.members import *
from cystack_models.models.users.users import User
from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.enterprises.members.enterprise_member_roles import EnterpriseMemberRole


class EnterpriseMember(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    access_time = models.IntegerField()
    is_default = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)

    status = models.CharField(max_length=128, default=PM_MEMBER_STATUS_CONFIRMED)
    email = models.CharField(max_length=128, null=True)
    token_invitation = models.TextField(null=True, default=None)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enterprise_members", null=True)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="enterprise_members")
    role = models.ForeignKey(EnterpriseMemberRole, on_delete=models.CASCADE, related_name="enterprise_members")

    class Meta:
        db_table = 'e_members'
        unique_together = ('user', 'team', 'role')

    @classmethod
    def create_multiple(cls, enterprise: Enterprise, *members: [Dict]):
        for member in members:
            try:
                cls.create(
                    enterprise=enterprise,
                    user=member["user"],
                    role_id=member["role"].name,
                    is_primary=member.get("is_primary", False),
                    is_default=member.get("is_default", False)
                )
            except:
                continue

    @classmethod
    def create(cls, enterprise: Enterprise, role_id: str, is_primary=False, is_default=False,
               status=PM_MEMBER_STATUS_CONFIRMED, user: User=None, email: str = None):
        new_member = EnterpriseMember.objects.create(
            user=user, email=email, role_id=role_id, enterprise=enterprise, access_time=now(),
            is_primary=is_primary,
            is_default=is_default,
            status=status
        )
        return new_member
