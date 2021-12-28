from shared.constants.members import *
from shared.permissions.locker_permissions.app import LockerPermission


class SharingPwdPermission(LockerPermission):
    scope = 'cipher'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        if view.action in ["public_key"]:
            return True
        return super(SharingPwdPermission, self).has_object_permission(request, view, obj)

    def get_role_pattern(self, view):
        return super(SharingPwdPermission, self).get_role_pattern(view)