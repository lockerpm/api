from shared.constants.members import MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN
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
        return role_name in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]
