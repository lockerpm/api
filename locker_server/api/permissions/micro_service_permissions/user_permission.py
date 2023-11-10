from locker_server.api.permissions.app import APIPermission


class UserPermission(APIPermission):
    def has_permission(self, request, view):
        if view.action in ["retrieve", "first_login", "search_by_device", "search_by_user"]:
            return True
        return super(UserPermission, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return super(UserPermission, self).has_object_permission(request, view, obj)
