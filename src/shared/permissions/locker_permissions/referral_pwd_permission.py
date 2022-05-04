from shared.permissions.locker_permissions.app import LockerPermission


class ReferralPwdPermission(LockerPermission):
    def has_permission(self, request, view):
        return self.is_auth(request)
