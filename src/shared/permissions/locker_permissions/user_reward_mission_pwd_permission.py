from shared.permissions.locker_permissions.app import LockerPermission


class UserRewardMissionPwdPermission(LockerPermission):
    def has_permission(self, request, view):
        if view.action in []:
            return True
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj)
