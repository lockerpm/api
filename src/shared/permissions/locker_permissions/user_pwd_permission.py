from shared.permissions.locker_permissions.app import LockerPermission


class UserPwdPermission(LockerPermission):
    def has_permission(self, request, view):
        if view.action in ["password_hint"]:
            return True
        if view.action in ["register", "prelogin", "me", "session"]:
            return self.is_auth(request)
        elif view.action in ["retrieve", "dashboard", "list_user_ids"]:
            return self.is_admin(request)
        return self.is_auth(request) and request.user.activated
