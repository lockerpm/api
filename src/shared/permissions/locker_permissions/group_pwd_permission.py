from shared.permissions.locker_permissions.app import LockerPermission


class GroupPwdPermission(LockerPermission):
    scope = 'group'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        return super(GroupPwdPermission, self).has_object_permission(request, view, obj)

    def get_role_pattern(self, view):
        if view.action == "users":
            if view.request.method == "PUT":
                return "{}.update".format(self.scope)
            return "{}.retrieve".format(self.scope)
        # map_action_to_perm = {}
        # if view.action in list(map_action_to_perm.keys()):
        #     return "{}.{}".format(self.scope, map_action_to_perm.get(view.action))
        return super(GroupPwdPermission, self).get_role_pattern(view)
