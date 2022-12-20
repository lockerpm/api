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
        if view.action in ["retrieve", "share_members", "cipher_use"]:
            return self.can_retrieve_cipher(request, obj)
        return False
        # return super(CipherPwdPermission, self).has_object_permission(request, view, obj.team)

    def get_role_pattern(self, view):
        return super(CipherPwdPermission, self).get_role_pattern(view)
