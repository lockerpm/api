from shared.permissions.micro_service_permissions.app import MicroServicePermission


class MobilePaymentPermission(MicroServicePermission):
    def has_permission(self, request, view):
        if view.action in ["upgrade_plan"]:
            return True
        return super(MobilePaymentPermission, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if view.action in ["upgrade_plan"]:
            return True
        return super(MobilePaymentPermission, self).has_object_permission(request, view, obj)
