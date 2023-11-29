from locker_server.api.permissions.app import APIPermission


class SSOConfigurationPermission(APIPermission):
    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.is_super_admin

    def has_object_permission(self, request, view, obj):
        user = request.user
        if view.action in ["sso_configuration", "update_sso_configuration", "destroy_sso_configuration"]:
            return user.is_super_admin and obj.created_by.user_id == user.user_id
        return request.user
