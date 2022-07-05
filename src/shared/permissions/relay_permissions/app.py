from shared.permissions.app import AppBasePermission


class RelayPermission(AppBasePermission):
    def has_permission(self, request, view):
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        return super(RelayPermission, self).has_object_permission(request, view, obj)
