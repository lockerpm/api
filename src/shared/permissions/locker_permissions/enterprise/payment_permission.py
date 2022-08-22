from shared.constants.enterprise_members import E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN
from shared.permissions.locker_permissions.enterprise.enterprise_permission import EnterprisePwdPermission


class PaymentPwdPermission(EnterprisePwdPermission):
    scope = 'payment'

    def has_permission(self, request, view):
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        member = self.get_team_member(user=request.user, obj=obj)
        role = member.role
        role_name = role.name
        if view.action in ["cards"]:
            if request.method == "POST":
                return role_name in [E_MEMBER_ROLE_PRIMARY_ADMIN]
        return role_name in [E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN]
