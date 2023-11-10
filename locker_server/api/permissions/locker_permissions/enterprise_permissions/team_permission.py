from locker_server.api.permissions.locker_permissions.enterprise_permissions.enterprise_pwd_permission import \
    EnterprisePwdPermission
from locker_server.shared.constants.members import MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN


class TeamPwdPermission(EnterprisePwdPermission):
    scope = 'team'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        action = view.action
        member = self.get_enterprise_member(user=request.user, obj=obj)
        role = member.role
        role_name = role.name
        if action in ["dashboard", "purge"]:
            return role_name in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]

        return super().has_object_permission(request, view, obj)
