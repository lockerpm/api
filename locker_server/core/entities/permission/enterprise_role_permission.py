from locker_server.core.entities.enterprise.member.enterprise_member_role import EnterpriseMemberRole
from locker_server.core.entities.permission.permission import Permission


class EnterpriseRolePermission(object):
    def __init__(self, enterprise_role: EnterpriseMemberRole, permission: Permission):
        self._enterprise_role = enterprise_role
        self._permission = permission

    @property
    def enterprise_role(self):
        return self._enterprise_role

    @property
    def permission(self):
        return self._permission
