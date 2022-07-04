from shared.permissions.locker_permissions.app import LockerPermission


class FormSubmissionPermission(LockerPermission):
    def has_permission(self, request, view):
        if view.action in ["create"]:
            return True
        return self.is_admin(request)
