from django.db import models

from locker_server.api_orm.models.permissions.permissions import PermissionORM
from locker_server.settings import locker_server_settings


class RolePermissionORM(models.Model):
    role = models.ForeignKey(
        locker_server_settings.LS_MEMBER_ROLE_MODEL, on_delete=models.CASCADE, related_name="role_permissions"
    )
    permission = models.ForeignKey(PermissionORM, on_delete=models.CASCADE, related_name="role_permissions")

    class Meta:
        db_table = 'cs_role_permissions'
        unique_together = ('role', 'permission')

    @classmethod
    def create(cls, role, permission):
        new_role_permission = cls(role=role, permission=permission)
        new_role_permission.save()
        return new_role_permission
