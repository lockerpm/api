from shared.permissions.locker_permissions.app import LockerPermission


class TeamCollectionPwdPermission(LockerPermission):
    scope = 'collection'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        return super(TeamCollectionPwdPermission, self).has_object_permission(request, view, obj)
