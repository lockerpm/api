from rest_framework.response import Response
from rest_framework.decorators import action

from shared.permissions.locker_permissions.payment_pwd_permission import PaymentPwdPermission
from shared.services.pm_sync import PwdSync, SYNC_EVENT_CIPHER_DELETE, SYNC_EVENT_CIPHER_CREATE
from v1_0.ciphers.serializers import VaultItemSerializer, MutipleItemIdsSerializer, MultipleMoveSerializer
from v1_0.resources.serializers import PMPlanSerializer
from v1_0.apps import PasswordManagerViewSet


class PaymentPwdViewSet(PasswordManagerViewSet):
    permission_classes = (PaymentPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        if self.action == "calc":
            pass
        
        return super(PaymentPwdViewSet, self).get_serializer_class()

    def get_invoice(self):
        pass

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        return super(PaymentPwdViewSet, self).list(request, *args, **kwargs)

    @action(methods=["post"], detail=False)
    def calc(self, request, *args, **kwargs):
        pass

    @action(methods=["get"], detail=False)
    def current_plan(self, request, *args, **kwargs):
        user = self.request.user
        pm_current_plan = self.user_repository.get_current_plan(user=user)
        next_billing_time = pm_current_plan.get_next_billing_time()
        result = PMPlanSerializer(pm_current_plan.pm_plan, many=False).data
        result.update({
            "next_billing_time": next_billing_time,
            "duration": pm_current_plan.duration,
            "subscribing": pm_current_plan.is_subscription(),
            "cancel_at_period_end": pm_current_plan.is_cancel_at_period_end(),
            "payment_method": pm_current_plan.get_default_payment_method(),
            "number_members": pm_current_plan.get_current_number_members()
        })
        return Response(status=200, data=result)
