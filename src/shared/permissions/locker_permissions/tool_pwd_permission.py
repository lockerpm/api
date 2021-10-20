from shared.permissions.locker_permissions.app import LockerPermission


class ToolPwdPermission(LockerPermission):
    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated
