import uuid
from typing import Dict

from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED, E_MEMBER_STATUS_INVITED
from locker_server.shared.utils.app import now


class AbstractEnterpriseMemberORM(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    access_time = models.IntegerField()
    is_default = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    is_activated = models.BooleanField(default=True)

    status = models.CharField(max_length=128, default=E_MEMBER_STATUS_CONFIRMED)
    email = models.CharField(max_length=128, null=True)
    token_invitation = models.TextField(null=True, default=None)
    user = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="enterprise_members", null=True
    )
    enterprise = models.ForeignKey(
        locker_server_settings.LS_ENTERPRISE_MODEL, on_delete=models.CASCADE, related_name="enterprise_members"
    )
    role = models.ForeignKey(
        locker_server_settings.LS_ENTERPRISE_MEMBER_ROLE_MODEL, on_delete=models.CASCADE,
        related_name="enterprise_members"
    )
    domain = models.ForeignKey(
        locker_server_settings.LS_ENTERPRISE_DOMAIN_MODEL, on_delete=models.SET_NULL,
        related_name="enterprise_members", null=True, default=None
    )

    class Meta:
        abstract = True
        unique_together = ('user', 'enterprise', 'role')

    @classmethod
    def create_multiple(cls, enterprise, *members: [Dict]):
        for member in members:
            try:
                cls.create(
                    enterprise=enterprise,
                    user=member["user"],
                    role_id=member["role"].name,
                    is_primary=member.get("is_primary", False),
                    is_default=member.get("is_default", False),
                    status=member.get("status") or E_MEMBER_STATUS_INVITED
                )
            except:
                continue

    @classmethod
    def create(cls, enterprise, role_id: str, is_primary=False, is_default=False,
               status=E_MEMBER_STATUS_INVITED, user=None, email: str = None):
        new_member = cls.objects.create(
            user=user, email=email, role_id=role_id, enterprise=enterprise, access_time=now(),
            is_primary=is_primary,
            is_default=is_default,
            status=status
        )
        return new_member

    @classmethod
    def multiple_retrieve_or_create(cls, enterprise, *members: [Dict]):
        for member_data in members:
            user = member_data.get("user")
            email = member_data.get("email")
            if email:
                cls.objects.get_or_create(
                    enterprise=enterprise, email=email, defaults={
                        "enterprise": enterprise,
                        "user": user,
                        "role_id": member_data.get("role_id"),
                        "domain": member_data.get("domain"),
                        "status": member_data.get("status", E_MEMBER_STATUS_INVITED),
                        "is_default": member_data.get("is_default", False),
                        "is_primary": member_data.get("is_primary", False),
                        "access_time": now(),
                    }
                )
            else:
                cls.objects.get_or_create(
                    enterprise=enterprise, user=user, defaults={
                        "enterprise": enterprise,
                        "email": email,
                        "role_id": member_data.get("role_id"),
                        "domain": member_data.get("domain"),
                        "status": member_data.get("status", E_MEMBER_STATUS_INVITED),
                        "is_default": member_data.get("is_default", False),
                        "is_primary": member_data.get("is_primary", False),
                        "access_time": now(),
                    }
                )

    @classmethod
    def retrieve_or_create_by_user(cls, enterprise, user, role_id: str, **data):
        member, is_created = cls.objects.get_or_create(
            enterprise=enterprise, user=user, defaults={
                "enterprise": enterprise,
                "user": user,
                "role_id": role_id,
                "domain": data.get("domain"),
                "status": data.get("status", E_MEMBER_STATUS_INVITED),
                "is_default": data.get("is_default",  False),
                "is_primary": data.get("is_primary", False),
                "access_time": now(),
            }
        )
        return member
