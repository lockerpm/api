from shared.permissions.locker_permissions.app import LockerPermission


class UserPwdPermission(LockerPermission):
    def has_permission(self, request, view):
        if view.action in ["password_hint", "invitation_confirmation"]:
            return True
        if view.action in ["prelogin", "me", "session", "passwordless_require"]:
            return self.is_auth(request)
        elif view.action in ["register"]:
            return self.is_auth(request) and request.user.activated is False
        elif view.action in ["retrieve", "dashboard", "list_users", "list_user_ids", "destroy"]:
            return self.is_admin(request)
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        return super(UserPwdPermission, self).has_object_permission(request, view, obj)