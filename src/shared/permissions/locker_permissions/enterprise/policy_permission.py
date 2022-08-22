from shared.constants.enterprise_members import *
from shared.permissions.locker_permissions.enterprise.enterprise_permission import EnterprisePwdPermission


class PolicyPwdPermission(EnterprisePwdPermission):
    scope = 'policy'

    def has_permission(self, request, view):
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        member = self.get_team_member(user=request.user, obj=obj)
        role = member.role
        role_name = role.name
        if view.action in ["list", "retrieve"]:
            return role_name in [E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN, E_MEMBER_ROLE_MEMBER]
        return role_name in [E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN]
