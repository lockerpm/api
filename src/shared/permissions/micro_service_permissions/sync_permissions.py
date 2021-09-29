from shared.permissions.micro_service_permissions.app import MicroServicePermission


class SyncPermission(MicroServicePermission):
    def has_permission(self, request, view):
        return super(SyncPermission, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return True
