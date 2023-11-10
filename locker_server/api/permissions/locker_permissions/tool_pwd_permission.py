
from locker_server.api.permissions.app import APIPermission


class ToolPwdPermission(APIPermission):
    def has_permission(self, request, view):
        if view.action in ["public_breach"]:
            return True
        return self.is_auth(request) and request.user.activated
