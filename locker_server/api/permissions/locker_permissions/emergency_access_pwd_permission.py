from locker_server.api.permissions.app import APIPermission


class EmergencyAccessPwdPermission(APIPermission):
    # scope = 'emergency_access'

    def has_permission(self, request, view):
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        user = request.user

        # obj is a EmergencyAsset object => Check user is a grantor or a grantee
        if view.action in ["reinvite", "confirm", "approve", "reject"]:
            return user.user_id == obj.grantor.user_id
        elif view.action in ["accept", "initiate", "view", "takeover", "password", "id_password"]:
            return obj.grantee and user.user_id == obj.grantee.user_id
        return user.user_id in [obj.grantee.user_id, obj.grantor.user_id] if obj.grantee else \
            user.user_id in [obj.grantor.user_id]
