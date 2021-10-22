from shared.permissions.locker_permissions.app import LockerPermission


class TeamCollectionPwdPermission(LockerPermission):
    scope = 'collection'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        return super(TeamCollectionPwdPermission, self).has_object_permission(request, view, obj)

    def get_role_pattern(self, view):
        if view.action == "users":
            if view.request.method == "PUT":
                return "{}.update".format(self.scope)
            return "{}.retrieve".format(self.scope)
        return super(TeamCollectionPwdPermission, self).get_role_pattern(view)