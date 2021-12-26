from shared.permissions.micro_service_permissions.app import MicroServicePermission


class UserPermission(MicroServicePermission):
    def has_permission(self, request, view):
        if view.action in ["first_login"]:
            return True
        return super(UserPermission, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return super(UserPermission, self).has_object_permission(request, view, obj)
