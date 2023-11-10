from locker_server.api.permissions.app import APIPermission


class ImportPwdPermission(APIPermission):
    scope = 'import_data'

    def has_permission(self, request, view):
        return self.is_auth(request) and request.user.activated

    def has_object_permission(self, request, view, obj):
        """

        :param request:
        :param view:
        :param obj:
        :return:
        """
        return super(ImportPwdPermission, self).has_object_permission(request, view, obj)

