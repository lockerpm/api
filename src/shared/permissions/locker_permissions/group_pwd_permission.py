from shared.permissions.locker_permissions.app import LockerPermission


class GroupPwdPermission(LockerPermission):
    scope = 'group'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        return super(GroupPwdPermission, self).has_object_permission(request, view, obj)


