from locker_server.api.permissions.app import APIPermission


class Factor2PwdPermission(APIPermission):
    def has_permission(self, request, view):
        if view.action in ["auth_otp_mail"]:
            return True
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj)
