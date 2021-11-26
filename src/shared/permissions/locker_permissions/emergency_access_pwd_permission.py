from shared.permissions.locker_permissions.app import LockerPermission


class EmergencyAccessPermission(LockerPermission):
    scope = 'emergency_access'

    def has_permission(self, request, view):
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        return super(EmergencyAccessPermission, self).has_object_permission(request, view, obj)
