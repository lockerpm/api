from django.db import models

from cystack_models.models.permissions.permissions import Permission
from cystack_models.models.enterprises.members.enterprise_member_roles import EnterpriseMemberRole


class EnterpriseRolePermission(models.Model):
    enterprise_role = models.ForeignKey(
        EnterpriseMemberRole, on_delete=models.CASCADE, related_name="enterprise_role_permissions"
    )
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="enterprise_role_permissions")

    class Meta:
        db_table = 'e_role_permissions'
        unique_together = ('enterprise_role', 'permission')

    @classmethod
    def create(cls, enterprise_role, permission):
        new_enterprise_role_permission = cls(enterprise_role=enterprise_role, permission=permission)
        new_enterprise_role_permission.save()
        return new_enterprise_role_permission
