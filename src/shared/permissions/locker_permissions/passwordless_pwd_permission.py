from shared.permissions.locker_permissions.app import LockerPermission


class PasswordlessPwdPermission(LockerPermission):
    def has_permission(self, request, view):
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        return super(PasswordlessPwdPermission, self).has_object_permission(request, view, obj)
