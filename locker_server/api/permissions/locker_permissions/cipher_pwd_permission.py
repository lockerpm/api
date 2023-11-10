from locker_server.api.permissions.app import APIPermission


class CipherPwdPermission(APIPermission):
    scope = 'cipher'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        if view.action in ["update", "share"]:
            return self.can_edit_cipher(request, obj)
        if view.action in ["retrieve", "share_members", "cipher_use"]:
            return self.can_retrieve_cipher(request, obj)
        return False
