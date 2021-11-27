from shared.permissions.locker_permissions.app import LockerPermission


class EmergencyAccessPermission(LockerPermission):
    scope = 'emergency_access'

    def has_permission(self, request, view):
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        user = request.user

        # obj is a EmergencyAsset object => Check user is a grantor or a grantee
        if view.action in ["reinvite", "confirm"]:
            return user.user_id == obj.grantor_id
        elif view.action in ["accept"]:
            return user.user_id == obj.grantee_id
        return user.user_id in [obj.grantee_id, obj.grantor_id]
