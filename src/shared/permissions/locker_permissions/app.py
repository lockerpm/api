from shared.permissions.app import AppBasePermission


class LockerPermission(AppBasePermission):
    def has_permission(self, request, view):
        return super(LockerPermission, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        member = self.get_team_member(user=request.user, obj=obj)
        role = member.role
        role_permissions = role.get_permissions()
        role_pattern = self.get_role_pattern(view)
        return role_pattern in role_permissions
