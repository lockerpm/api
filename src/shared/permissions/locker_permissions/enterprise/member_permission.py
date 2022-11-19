from shared.constants.enterprise_members import E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN, E_MEMBER_ROLE_MEMBER
from shared.permissions.locker_permissions.enterprise.enterprise_permission import EnterprisePwdPermission


class MemberPwdPermission(EnterprisePwdPermission):
    scope = 'member'

    def has_permission(self, request, view):
        return self.is_auth(request)        # and request.user.activated

    def has_object_permission(self, request, view, obj):
        member = self.get_team_member(user=request.user, obj=obj)
        role = member.role
        role_name = role.name
        if view.action == "search_members_groups":
            return role_name in [E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN, E_MEMBER_ROLE_MEMBER]
        return role_name in [E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN]
