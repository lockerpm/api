from locker_server.api.permissions.locker_permissions.enterprise_permissions.enterprise_pwd_permission import \
    EnterprisePwdPermission
from locker_server.shared.constants.enterprise_members import E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN


class DomainPwdPermission(EnterprisePwdPermission):
    scope = 'domain'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        if self.is_super_admin(request):
            return True
        member = self.get_enterprise_member(user=request.user, obj=obj)
        role = member.role
        role_name = role.name
        return role_name in [E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN]
