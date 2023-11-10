from locker_server.api.permissions.app import APIPermission


class RelayHookPermission(APIPermission):
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return True
