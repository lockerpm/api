from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from cystack_models.factory.payment_method.payment_method_factory import PaymentMethodFactory
from cystack_models.models.enterprises.enterprises import Enterprise
from cystack_models.models.payments.payment_items import PaymentItem
from cystack_models.models.payments.payments import Payment
from cystack_models.models.user_plans.pm_plans import PMPlan
from shared.constants.transactions import *
from shared.error_responses.error import gen_error
from shared.permissions.locker_permissions.enterprise.payment_permission import PaymentPwdPermission
from shared.utils.app import now
from v1_0.resources.serializers import PMPlanSerializer
from v1_enterprise.apps import EnterpriseViewSet
from .serializers import InvoiceSerializer, CalcSerializer, UpgradePlanSerializer, BillingAddressSerializer


class PaymentPwdViewSet(EnterpriseViewSet):
    permission_classes = (PaymentPwdPermission, )
    http_method_names = ["head", "options", "get", "post", "put"]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            self.serializer_class = InvoiceSerializer
        elif self.action == "calc":
            self.serializer_class = CalcSerializer
        elif self.action == "upgrade_plan":
            self.serializer_class = UpgradePlanSerializer
        elif self.action == "billing_address":
            self.serializer_class = BillingAddressSerializer
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
        invoices = Payment.objects.filter(enterprise_id=enterprise.id).order_by('-created_time')
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

    def get_object(self):
        enterprise = self.get_enterprise()
        try:
            invoice = Payment.objects.get(enterprise_id=enterprise.id, payment_id=self.kwargs.get("payment_id"))
            return invoice
        except Payment.DoesNotExist:
            raise NotFound

    def list(self, request, *args, **kwargs):
        paging_param = self.request.query_params.get("paging", "1")
        page_size_param = self.check_int_param(self.request.query_params.get("size", 10))
        if paging_param == "0":
            self.pagination_class = None
        else:
            self.pagination_class.page_size = page_size_param if page_size_param else 10
        return super(PaymentPwdViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super(PaymentPwdViewSet, self).retrieve(request, *args, **kwargs)

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
            "enterprise": {
                "current_members": enterprise.get_activated_members_count()
            },
            "stripe_subscription": current_plan.pm_stripe_subscription,
            "primary_admin": primary_admin.user_id
        })
        return Response(status=200, data=result)

    @action(methods=["get", "post"], detail=False)
    def cards(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        primary_admin = enterprise.enterprise_members.get(is_primary=True).user
        primary_admin_plan = self.user_repository.get_current_plan(user=primary_admin, scope=settings.SCOPE_PWD_MANAGER)
        stripe_subscription = primary_admin_plan.get_stripe_subscription()
        stripe_default_payment_method = stripe_subscription.default_payment_method if stripe_subscription else None
        return Response(status=200, data={
            "primary_admin": primary_admin.user_id,
            "stripe_default_payment_method": stripe_default_payment_method
        })

    @action(methods=["put"], detail=False)
    def card_set_default(self, request, *args, **kwargs):
        card_id = kwargs.get("card_id")
        enterprise = self.get_enterprise()
        primary_admin = enterprise.enterprise_members.get(is_primary=True).user
        primary_admin_plan = self.user_repository.get_current_plan(user=primary_admin, scope=settings.SCOPE_PWD_MANAGER)
        stripe_subscription = primary_admin_plan.get_stripe_subscription()
        if not stripe_subscription:
            return Response(status=200, data={"stripe_payment_method": None})
        payment = PaymentMethodFactory.get_method(
            user=primary_admin, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_CARD
        )
        new_source = payment.update_default_payment(new_source=card_id)
        return Response(status=200, data={"stripe_payment_method": new_source})

    @action(methods=["post"], detail=False)
    def calc(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        promo_code = validated_data.get("promo_code")
        duration = validated_data.get("duration", DURATION_MONTHLY)
        currency = validated_data.get("currency", CURRENCY_USD)
        # Calc payment
        result = self._calc_payment(
            enterprise=enterprise, duration=duration, currency=currency, promo_code=promo_code
        )
        return Response(status=200, data=result)

    @action(methods=["post"], detail=False)
    def upgrade_plan(self, request, *args, **kwargs):
        user = self.request.user
        enterprise = self.get_enterprise()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        card = request.data.get("card")
        if not card:
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        if not card.get("id_card"):
            raise ValidationError({"non_field_errors": [gen_error("7007")]})
        validated_data = serializer.validated_data
        promo_code_obj = validated_data.get("promo_code_obj", None)
        duration = validated_data.get("duration", DURATION_MONTHLY)
        number_members = enterprise.get_activated_members_count()
        currency = validated_data.get("currency")
        metadata = {
            "currency": currency,
            "promo_code": promo_code_obj,
            "card": card,
            "number_members": number_members,
            "enterprise_id": enterprise.id,
        }
        current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        if current_plan.get_plan_obj().is_team_plan is False:
            raise ValidationError(detail={"non_field_errors": [gen_error("7014")]})
        if current_plan.end_period and current_plan.end_period > now():
            metadata.update({
                "trial_end": int(current_plan.end_period - now())
            })
        # Calc payment price of new plan
        promo_code_value = promo_code_obj.code if promo_code_obj else None
        calc_payment = self._calc_payment(
            enterprise=enterprise, duration=duration, currency=currency, promo_code=promo_code_value
        )
        immediate_payment = calc_payment.get("immediate_payment")

        payment = PaymentMethodFactory.get_method(
            user=user, scope=settings.SCOPE_PWD_MANAGER, payment_method=PAYMENT_METHOD_CARD
        )
        payment_result = payment.upgrade_recurring_subscription(
            amount=immediate_payment, plan_type=PLAN_TYPE_PM_ENTERPRISE, coupon=promo_code_obj, duration=duration,
            **metadata
        )
        update_result = payment_result.get("success")
        if update_result is False:
            if payment_result.get("stripe_error"):
                return Response(status=400, data={
                    "code": "7009",
                    "message": "Your card was declined (insufficient funds, etc...)",
                    "details": payment_result.get("error_details")
                })
            raise ValidationError({"non_field_errors": [gen_error("7009")]})

        # Set default payment method
        try:
            current_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
            current_plan.set_default_payment_method(PAYMENT_METHOD_CARD)
        except ObjectDoesNotExist:
            pass
        return Response(status=200, data={"success": True})

    @action(methods=["get", "put"], detail=False)
    def billing_address(self, request, *args, **kwargs):
        enterprise = self.get_enterprise()
        if request.method == "GET":
            return Response(status=200, data=self.get_serializer(enterprise).data)

        elif request.method == "PUT":
            partial = kwargs.pop('partial', False)
            serializer = self.get_serializer(enterprise, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            if getattr(enterprise, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                enterprise._prefetched_objects_cache = {}
            return Response(status=200, data=serializer.data)

    def _calc_payment(self, enterprise: Enterprise, duration=DURATION_MONTHLY, currency=CURRENCY_USD, promo_code=None):
        current_plan = self.user_repository.get_current_plan(user=self.request.user, scope=settings.SCOPE_PWD_MANAGER)
        plan = PMPlan.objects.get(alias=PLAN_TYPE_PM_ENTERPRISE)
        quantity = enterprise.get_activated_members_count()
        result = current_plan.calc_update_price(
            new_plan=plan, new_duration=duration,
            new_quantity=quantity,
            currency=currency, promo_code=promo_code
        )
        result["quantity"] = quantity
        result["plan"] = PMPlanSerializer(plan, many=False).data
        return result