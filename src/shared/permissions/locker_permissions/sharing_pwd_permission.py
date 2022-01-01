from shared.constants.members import *
from shared.permissions.locker_permissions.app import LockerPermission


class SharingPwdPermission(LockerPermission):
    # scope = 'cipher'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        if view.action in ["public_key"]:
            return True
        member = self.get_team_member(user=request.user, obj=obj)
        role = member.role
        if view.action in ["leave"]:
            return role.name in [MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER]

        return role.name in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]
