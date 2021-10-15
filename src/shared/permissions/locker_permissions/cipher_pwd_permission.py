from shared.permissions.locker_permissions.app import LockerPermission


class CipherPwdPermission(LockerPermission):
    scope = 'cipher'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        member = self.get_team_member(user=request.user, obj=obj)
        role = member.role
        role_permissions = role.get_permissions()
        role_pattern = self.get_role_pattern(view)
        return role_pattern in role_permissions

    def get_role_pattern(self, view):
        # map_action_to_perm = {
        #     "share_users": "retrieve",
        # }
        # if view.action in list(map_action_to_perm.keys()):
        #     return "{}.{}".format(self.scope, map_action_to_perm.get(view.action))
        return super(CipherPwdPermission, self).get_role_pattern(view)
