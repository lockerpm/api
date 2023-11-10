from django.conf import settings

from locker_server.api.permissions.app import APIPermission


class ReleasePwdPermission(APIPermission):
    def has_permission(self, request, view):
        if view.action in ["current_version", "list", "retrieve"]:
            return True
        elif view.action in ["new", "current"]:
            return self.is_management_command(request)
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        return False

    @staticmethod
    def is_management_command(request):
        token = request.query_params.get("token")
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        return token == settings.MANAGEMENT_COMMAND_TOKEN or auth_header == f"Token {settings.MANAGEMENT_COMMAND_TOKEN}"
