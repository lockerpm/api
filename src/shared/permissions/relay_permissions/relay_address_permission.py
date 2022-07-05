from shared.permissions.relay_permissions.app import RelayPermission


class RelayAddressPermission(RelayPermission):

    def has_permission(self, request, view):
        return self.is_auth(request)

    def has_object_permission(self, request, view, obj):
        # if view.action in ["destroy"]:
        #     return self.is_admin(request)
        return self.is_auth(request)

