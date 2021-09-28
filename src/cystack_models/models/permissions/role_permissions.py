from django.db import models

from cystack_models.models.members.member_roles import MemberRole
from cystack_models.models.permissions.permissions import Permission


class RolePermission(models.Model):
    role = models.ForeignKey(MemberRole, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="role_permissions")

    class Meta:
        db_table = 'cs_role_permissions'
        unique_together = ('role', 'permission')

    @classmethod
    def create(cls, role, permission):
        new_role_permission = cls(
            role=role, permission=permission
        )
        new_role_permission.save()
        return new_role_permission
