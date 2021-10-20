from shared.constants.members import *
from shared.permissions.locker_permissions.app import LockerPermission


class CipherPwdPermission(LockerPermission):
    scope = 'cipher'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        """

        :param request:
        :param view:
        :param obj: (obj) Cipher object
        :return:
        """
        if view.action in ["update", "share"]:
            member = self.get_team_member(user=request.user, obj=obj.team)
            # Check is owner or admin
            role_id = member.role_id
            is_owner_or_admin = role_id in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]
            # Check is a member of access all groups
            group_access_all = obj.team.groups.filter(access_all=True).values_list('id', flat=True)
            is_allow_group = member.groups_members.filter(group_id__in=list(group_access_all)).exists()
            return is_allow_group or is_owner_or_admin

        return super(CipherPwdPermission, self).has_object_permission(request, view, obj)

    def get_role_pattern(self, view):
        map_action_to_perm = {
            "multiple_delete": "destroy",
            "multiple_permanent_delete": "destroy",
            "multiple_restore": "destroy",
            "vaults": "create"
        }
        if view.action in list(map_action_to_perm.keys()):
            return "{}.{}".format(self.scope, map_action_to_perm.get(view.action))
        return super(CipherPwdPermission, self).get_role_pattern(view)
