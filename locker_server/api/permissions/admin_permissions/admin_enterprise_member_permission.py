from locker_server.api.permissions.admin_permissions.admin_enterprise_permission import AdminEnterprisePermission
from locker_server.shared.constants.enterprise_members import E_MEMBER_ROLE_PRIMARY_ADMIN


class AdminEnterpriseMemberPermission(AdminEnterprisePermission):

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.is_super_admin

    def has_object_permission(self, request, view, obj):
        if view.action in ["list", "retrieve", "update", "activated", "destroy"]:
            return request.user.is_super_admin
        return super().has_object_permission(request, view, obj)
