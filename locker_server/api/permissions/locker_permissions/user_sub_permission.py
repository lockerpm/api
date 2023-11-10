from locker_server.api.permissions.app import APIPermission


class UserSubPermission(APIPermission):
    def has_permission(self, request, view):
        if self.is_admin(request):
            return True
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj)
