from django.conf import settings

from shared.permissions.locker_permissions.app import LockerPermission


class ReleasePwdPermission(LockerPermission):
    def has_permission(self, request, view):
        if view.action in ["new", "current"]:
            token = request.query_params.get("token")
            auth_header = request.META.get("HTTP_AUTHORIZATION")
            return token == settings.MANAGEMENT_COMMAND_TOKEN or \
                   auth_header == f"Token {settings.MANAGEMENT_COMMAND_TOKEN}"
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        return False
