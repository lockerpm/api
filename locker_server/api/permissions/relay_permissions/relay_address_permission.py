from locker_server.api.permissions.app import APIPermission


class RelayAddressPermission(APIPermission):
    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj)
