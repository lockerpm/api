from django.db import models

from locker_server.api_orm.models import PermissionORM
from locker_server.settings import locker_server_settings


class EnterpriseRolePermissionORM(models.Model):
    enterprise_role = models.ForeignKey(
        locker_server_settings.LS_ENTERPRISE_MEMBER_ROLE_MODEL, on_delete=models.CASCADE,
        related_name="enterprise_role_permissions"
    )
    permission = models.ForeignKey(PermissionORM, on_delete=models.CASCADE, related_name="enterprise_role_permissions")

    class Meta:
        db_table = 'e_role_permissions'
        unique_together = ('enterprise_role', 'permission')

    @classmethod
    def create(cls, enterprise_role, permission):
        new_enterprise_role_permission = cls(enterprise_role=enterprise_role, permission=permission)
        new_enterprise_role_permission.save()
        return new_enterprise_role_permission
