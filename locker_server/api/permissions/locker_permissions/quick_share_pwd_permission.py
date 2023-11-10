from locker_server.api.permissions.app import APIPermission


class QuickSharePwdPermission(APIPermission):
    # scope = 'quick_share'

    def has_permission(self, request, view):
        if view.action in ["public", "access", "otp"]:
            return True
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user

    # def get_role_pattern(self, view):
    #     return super().get_role_pattern(view)
