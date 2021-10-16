from shared.permissions.locker_permissions.app import LockerPermission


class TeamEventPwdPermission(LockerPermission):
    scope = 'event'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        return super(TeamEventPwdPermission, self).has_object_permission(request, view, obj)
