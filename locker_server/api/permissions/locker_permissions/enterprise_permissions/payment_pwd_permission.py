from locker_server.api.permissions.locker_permissions.enterprise_permissions.enterprise_pwd_permission import \
    EnterprisePwdPermission
from locker_server.shared.constants.enterprise_members import E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN, \
    E_MEMBER_ROLE_MEMBER


class EnterprisePaymentPwdPermission(EnterprisePwdPermission):
    scope = 'payment'

    def has_permission(self, request, view):
        if view.action in ["calc_public"]:
            return True
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        member = self.get_enterprise_member(user=request.user, obj=obj)
        role = member.role
        role_name = role.name
        if view.action in ["cards"]:
            if request.method == "POST":
                return role_name in [E_MEMBER_ROLE_PRIMARY_ADMIN]
        elif view.action in ["upgrade_plan", "calc", "card_set_default"]:
            return role_name in [E_MEMBER_ROLE_PRIMARY_ADMIN]
        elif view.action in ["billing_address"]:
            if request.method == "PUT":
                return role_name in [E_MEMBER_ROLE_PRIMARY_ADMIN]
        return role_name in [E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN]
