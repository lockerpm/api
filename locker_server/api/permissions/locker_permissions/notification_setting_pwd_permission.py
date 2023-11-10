from locker_server.api.permissions.app import APIPermission


class NotificationSettingPwdPermission(APIPermission):
    def has_permission(self, request, view):
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        return request.user.user_id == obj.user.user_id
