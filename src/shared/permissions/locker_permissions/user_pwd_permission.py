from shared.permissions.locker_permissions.app import LockerPermission


class UserPwdPermission(LockerPermission):
    def has_permission(self, request, view):
        if view.action in ["password_hint"]:
            return True
        return self.is_auth(request)
