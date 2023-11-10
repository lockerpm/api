from locker_server.api.permissions.app import APIPermission


class BackupCredentialPwdPermission(APIPermission):
    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        user = request.user
        return obj.user.user_id == user.user_id
