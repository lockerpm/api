from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import PermissionDenied

from shared.constants.enterprise_members import E_MEMBER_ROLE_ADMIN, E_MEMBER_ROLE_PRIMARY_ADMIN
from shared.permissions.locker_permissions.app import LockerPermission


class EnterprisePwdPermission(LockerPermission):
    scope = 'enterprise'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        action = view.action

        if action in ["dashboard"]:
            member = self.get_team_member(user=request.user, obj=obj)
            role = member.role
            role_name = role.name
            return role_name in [E_MEMBER_ROLE_PRIMARY_ADMIN, E_MEMBER_ROLE_ADMIN]
        return super(EnterprisePwdPermission, self).has_object_permission(request, view, obj)

    @staticmethod
    def get_team_member(user, obj):
        try:
            return obj.enterprise_members.get(user=user)
        except ObjectDoesNotExist:
            raise PermissionDenied

    def get_role(self, user, obj):
        member = self.get_team_member(user, obj)
        return member.role
