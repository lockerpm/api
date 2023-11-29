from locker_server.api.permissions.app import APIPermission


class AdminMailConfigurationPermission(APIPermission):

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.is_super_admin

    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_super_admin
