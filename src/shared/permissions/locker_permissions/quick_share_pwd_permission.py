from shared.permissions.locker_permissions.app import LockerPermission


class QuickSharePwdPermission(LockerPermission):
    scope = 'quick_share'

    def has_permission(self, request, view):
        if view.action in ["public", "access", "otp"]:
            return True
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        return False

    def get_role_pattern(self, view):
        return super().get_role_pattern(view)
