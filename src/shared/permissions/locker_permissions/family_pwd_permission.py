from shared.constants.members import *
from shared.permissions.locker_permissions.app import LockerPermission


class FamilyPwdPermission(LockerPermission):
    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        return super(FamilyPwdPermission, self).has_object_permission(request, view, obj)
