from locker_server.api.permissions.app import APIPermission


class PaymentPermission(APIPermission):
    def has_permission(self, request, view):
        if view.action in ["webhook_create", "webhook_set_status",
                           "webhook_unpaid_subscription", "webhook_cancel_subscription",
                           "banking_callback", "referral_payment",
                           "charge_set_status"]:
            return True
        return super(PaymentPermission, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if view.action in ["webhook_create", "webhook_set_status",
                           "webhook_unpaid_subscription", "webhook_cancel_subscription",
                           "banking_callback"]:
            return True
        return super(PaymentPermission, self).has_object_permission(request, view, obj)
