from shared.constants.members import MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER
from shared.permissions.locker_permissions.app import LockerPermission


class PolicyPwdPermission(LockerPermission):
    scope = 'team'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        action = view.action
        member = self.get_team_member(user=request.user, obj=obj)
        role = member.role
        role_name = role.name
        if action in ["retrieve"]:
            return role_name in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER]
        return role_name in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]
