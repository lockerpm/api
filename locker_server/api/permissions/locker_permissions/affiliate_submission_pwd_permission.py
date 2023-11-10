from locker_server.api.permissions.app import APIPermission


class AffiliateSubmissionPwdPermission(APIPermission):
    def has_permission(self, request, view):
        if view.action in ["create"]:
            return True
        return self.is_admin(request)

    def has_object_permission(self, request, view, obj):
        return self.is_admin(request)
