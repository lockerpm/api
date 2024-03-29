import uuid
from typing import Dict

import jwt
from django.conf import settings
from django.db import models

from shared.constants.token import TOKEN_EXPIRED_TIME_INVITE_MEMBER, TOKEN_TYPE_INVITE_MEMBER, TOKEN_PREFIX
from shared.utils.app import now
from shared.constants.enterprise_members import *
from cystack_models.models.users.users import User
from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.enterprises.domains.domains import Domain
from cystack_models.models.enterprises.members.enterprise_member_roles import EnterpriseMemberRole


class EnterpriseMember(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    access_time = models.IntegerField()
    is_default = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    is_activated = models.BooleanField(default=True)

    status = models.CharField(max_length=128, default=E_MEMBER_STATUS_CONFIRMED)
    email = models.CharField(max_length=128, null=True)
    token_invitation = models.TextField(null=True, default=None)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enterprise_members", null=True)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="enterprise_members")
    role = models.ForeignKey(EnterpriseMemberRole, on_delete=models.CASCADE, related_name="enterprise_members")
    domain = models.ForeignKey(
        Domain, on_delete=models.SET_NULL, related_name="enterprise_members", null=True, default=None
    )

    class Meta:
        db_table = 'e_members'
        unique_together = ('user', 'enterprise', 'role')

    @classmethod
    def create_multiple(cls, enterprise: Enterprise, *members: [Dict]):
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
    def create(cls, enterprise: Enterprise, role_id: str, is_primary=False, is_default=False,
               status=E_MEMBER_STATUS_INVITED, user: User=None, email: str = None):
        new_member = EnterpriseMember.objects.create(
            user=user, email=email, role_id=role_id, enterprise=enterprise, access_time=now(),
            is_primary=is_primary,
            is_default=is_default,
            status=status
        )
        return new_member

    @classmethod
    def multiple_retrieve_or_create(cls, enterprise: Enterprise, *members: [Dict]):
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
    def retrieve_or_create_by_user(cls, enterprise: Enterprise, user: User, role_id: str, **data):
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

    def create_invitation_token(self):
        if self.email:
            created_time = now()
            expired_time = created_time + TOKEN_EXPIRED_TIME_INVITE_MEMBER * 3600
            payload = {
                "scope": settings.SCOPE_PWD_MANAGER,
                "member": self.email,
                "enterprise": self.enterprise_id,
                "created_time": created_time,
                "expired_time": expired_time,
                "token_type": TOKEN_TYPE_INVITE_MEMBER
            }
            token_value = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
            token_value = TOKEN_PREFIX + token_value
        else:
            token_value = None
        self.token_invitation = token_value
        self.save()
        return token_value
