from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.payments.payment_items import PaymentItem
from cystack_models.models.payments.payments import Payment
from shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED
from shared.permissions.locker_permissions.enterprise.payment_permission import PaymentPwdPermission
from v1_0.resources.serializers import PMPlanSerializer
from v1_enterprise.apps import EnterpriseViewSet
from .serializers import InvoiceSerializer


class PaymentPwdViewSet(EnterpriseViewSet):
    permission_classes = (PaymentPwdPermission, )
    http_method_names = ["head", "options", "get", "post"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            self.serializer_class = InvoiceSerializer
        return super(PaymentPwdViewSet, self).get_serializer_class()

    def get_enterprise(self):
        try:
            enterprise = Enterprise.objects.get(id=self.kwargs.get("pk"))
            self.check_object_permissions(request=self.request, obj=enterprise)
            return enterprise
        except Enterprise.DoesNotExist:
            raise NotFound

    def get_queryset(self):
        enterprise = self.get_enterprise()
        payment_ids = PaymentItem.objects.filter(team_id=enterprise.id).values_list('payment_id', flat=True)
        invoices = Payment.objects.filter(id__in=payment_ids).order_by('-created_time')
        status_param = self.request.query_params.get("status")
        payment_method_param = self.request.query_params.get("payment_method")
        from_param = self.check_int_param(self.request.query_params.get("from"))
        to_param = self.check_int_param(self.request.query_params.get("to"))
        if to_param:
            invoices = invoices.filter(created_time__gt=to_param)
        if from_param:
            invoices = invoices.filter(created_time__lte=from_param)
        if status_param:
            invoices = invoices.filter(status=status_param)
        if payment_method_param:
            invoices = invoices.filter(payment_method=payment_method_param)
        return invoices

    def list(self, request, *args, **kwargs):
        return super(PaymentPwdViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        # TODO: Retrieve Enterprise's payment
        raise NotFound

    @action(methods=["get"], detail=False)
    def current_plan(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        primary_admin = enterprise.enterprise_members.get(is_primary=True).user
        current_plan = self.user_repository.get_current_plan(user=primary_admin)
        result = PMPlanSerializer(current_plan.get_plan_obj(), many=False).data
        result.update({
            "next_billing_time": current_plan.get_next_billing_time(),
            "duration": current_plan.duration,
            "is_trailing": current_plan.is_trailing(),
            "cancel_at_period_end": current_plan.is_cancel_at_period_end(),
            "payment_method": current_plan.get_default_payment_method(),
            # "number_members": current_plan.get_current_number_members(),
            "enterprise": {
                "current_members": enterprise.enterprise_members.filter(
                    status=E_MEMBER_STATUS_CONFIRMED, is_activated=True
                ).count()
            }
        })
        return Response(status=200, data=result)

    @action(methods=["get"], detail=False)
    def cards(self, request, *args, **kwargs):
        pass


