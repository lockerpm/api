from shared.permissions.locker_permissions.app import LockerPermission


class UserPwdPermission(LockerPermission):
    def has_permission(self, request, view):
        if view.action in ["password_hint"]:
            return True
        if view.action in ["register", "prelogin", "me", "session"]:
            return self.is_auth(request)
        elif view.action in ["retrieve", "dashboard", "list_user_ids", "destroy"]:
            return self.is_admin(request)
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        if view.action in ["password"]:
            return self.can_edit_cipher(request, obj)
        return super(UserPwdPermission, self).has_object_permission(request, view, obj)