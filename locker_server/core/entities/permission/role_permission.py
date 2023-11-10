from locker_server.core.entities.member.member_role import MemberRole
from locker_server.core.entities.permission.permission import Permission


class RolePermission(object):
    def __init__(self, role_permission_id: int, role: MemberRole, permission: Permission):
        self._role_permission_id = role_permission_id
        self._role = role
        self._permission = permission

    @property
    def role_permission_id(self):
        return self._role_permission_id

    @property
    def role(self):
        return self._role

    @property
    def permission(self):
        return self._permission
