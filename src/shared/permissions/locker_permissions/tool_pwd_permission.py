from shared.permissions.locker_permissions.app import LockerPermission


class ToolPwdPermission(LockerPermission):
    def has_permission(self, request, view):
        if view.action in ["public_breach"]:
            return True
        return self.is_auth(request) and request.user.activated
