from shared.constants.members import MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN
from shared.permissions.locker_permissions.app import LockerPermission


class MemberPwdPermission(LockerPermission):
    scope = 'member'

    def has_permission(self, request, view):
        if view.action in ["invitation_confirmation"]:
            return True
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        if view.action in ["invitation_confirmation"]:
            return True
        member = self.get_team_member(user=request.user, obj=obj)
        role = member.role
        return role.name in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]
