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
            return self.can_edit_cipher(request, obj)

        return super(CipherPwdPermission, self).has_object_permission(request, view, obj.team)

    def get_role_pattern(self, view):
        # map_action_to_perm = {
        #     "multiple_delete": "destroy",
        #     "multiple_permanent_delete": "destroy",
        #     "multiple_restore": "destroy",
        #     "vaults": "create"
        # }
        # if view.action in list(map_action_to_perm.keys()):
        #     return "{}.{}".format(self.scope, map_action_to_perm.get(view.action))
        return super(CipherPwdPermission, self).get_role_pattern(view)
