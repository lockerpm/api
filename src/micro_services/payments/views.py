import stripe

from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound

from micro_services.apps import MicroServiceViewSet
from shared.background import LockerBackgroundFactory, BG_NOTIFY
from shared.constants.transactions import *
from shared.permissions.micro_service_permissions.payment_permissions import PaymentPermission
from shared.utils.app import now
from cystack_models.models.payments.payments import Payment
from cystack_models.models.users.users import User
from v1_0.payments.serializers import DetailInvoiceSerializer
from micro_services.payments.serializers import InvoiceWebhookSerializer, PaymentStatusWebhookSerializer, \
    BankingCallbackSerializer


class PaymentViewSet(MicroServiceViewSet):
    permission_classes = (PaymentPermission, )
    http_method_names = ["head", "options", "post", "put"]

    def get_serializer_class(self):
        if self.action == "webhook_create":
            self.serializer_class = InvoiceWebhookSerializer
        elif self.action in ["webhook_set_status", "charge_set_status"]:
            self.serializer_class = PaymentStatusWebhookSerializer
        elif self.action == "banking_callback":
            self.serializer_class = BankingCallbackSerializer
        return super(PaymentViewSet, self).get_serializer_class()

    @action(methods=["post"], detail=False)
    def charge_set_status(self, request, *args, **kwargs):
        return Response(status=200, data={"success": True})

    @action(methods=["post"], detail=False)
    def webhook_create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        new_payment = result.get("new_payment")
        payment_data = result.get("payment_data", {})
        subtotal = new_payment.total_price + new_payment.discount
        return Response(status=200, data={
            "success": True,
            "user_id": new_payment.user.user_id,
            "status": new_payment.status,
            "paid": True if new_payment.status == PAYMENT_STATUS_PAID else False,
            "scope": new_payment.scope,
            "payment_id": new_payment.payment_id,
            "order_date": new_payment.get_created_time_str(),
            "total": new_payment.total_price,
            "subtotal": subtotal,
            "discount": new_payment.discount,
            "currency": new_payment.currency,
            "duration": new_payment.duration,
            "plan": new_payment.plan,
            "customer": new_payment.get_customer_dict(),
            "payment_method": new_payment.payment_method,
            "payment_data": payment_data
        })

    @action(methods=["post"], detail=False)
    def webhook_set_status(self, request, *args, **kwargs):
        invoice_id = kwargs.get("pk")
        try:
            payment = Payment.objects.get(payment_id=invoice_id)
        except Payment.DoesNotExist:
            raise NotFound
        user = payment.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        status = validated_data.get("status")
        failure_reason = validated_data.get("failure_reason")
        payment_data = {
            "user_id": user.user_id,
            "success": True,
            "payment_id": payment.payment_id,
            "order_date": payment.get_created_time_str(),
            "total_money": "{}".format(payment.total_price),
            "currency": payment.currency,
            "paid": True if status == PAYMENT_STATUS_PAID else False,
            "payment_method": PAYMENT_METHOD_CARD,
            "created_time": payment.created_time
        }
        current_plan = self.user_repository.get_current_plan(user=user, scope=payment.scope)
        payment_data.update({
            "current_plan": current_plan.get_plan_type_name(),
            "total_price": payment.total_price,
            "duration": payment.duration,
            "plan_price": current_plan.pm_plan.get_price(duration=payment.duration, currency=payment.currency),
            "url": "{}/invoices/{}".format(settings.LOCKER_WEB_URL, payment.payment_id),
        })

        if status == PAYMENT_STATUS_PAID:
            self.payment_repository.set_paid(payment=payment)
        elif status == PAYMENT_STATUS_PAST_DUE:
            self.payment_repository.set_past_due(payment=payment, failure_reason=failure_reason)
            payment_data.update({"reason": failure_reason})
        elif status == PAYMENT_STATUS_FAILED:
            self.payment_repository.set_failed(payment=payment, failure_reason=failure_reason)
            payment_data.update({"reason": failure_reason})
        return Response(status=200, data=payment_data)

    @action(methods=["post"], detail=False)
    def webhook_unpaid_subscription(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        scope = self.request.query_params.get("scope", settings.SCOPE_PWD_MANAGER)
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            raise NotFound
        current_plan = self.user_repository.get_current_plan(user=user, scope=scope)
        stripe_subscription = current_plan.get_stripe_subscription()
        if stripe_subscription:
            stripe.Subscription.retrieve(stripe_subscription.id).delete()
        return Response(status=200, data={"user_id": user_id})

    @action(methods=["put"], detail=False)
    def webhook_cancel_subscription(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        scope = self.request.query_params.get("scope", settings.SCOPE_PWD_MANAGER)
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            raise NotFound
        payment_data = {}
        current_plan = self.user_repository.get_current_plan(user=user, scope=scope)
        old_plan = current_plan.get_plan_type_name()
        current_plan.cancel_stripe_subscription()
        self.user_repository.update_plan(user=user, plan_type_alias=PLAN_TYPE_PM_FREE, scope=scope)

        # Notify downgrade here
        LockerBackgroundFactory.get_background(
            bg_name=BG_NOTIFY, background=True
        ).run(func_name="downgrade_plan", **{
            "user_id": user.user_id, "old_plan": old_plan, "downgrade_time": now(),
            "scope": settings.SCOPE_PWD_MANAGER, **{"payment_data": payment_data}
        })
        return Response(status=200, data={"old_plan": old_plan})

    @action(methods=["post"], detail=False)
    def banking_callback(self, request, *arg, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        amount = validated_data.get("amount")
        code = validated_data.get("code")

        # Retrieve invoice
        try:
            invoice = Payment.objects.get(
                payment_method=PAYMENT_METHOD_BANKING, code=code,
                status__in=[PAYMENT_STATUS_PENDING, PAYMENT_STATUS_PROCESSING]
            )
        except Payment.DoesNotExist:
            raise NotFound
        if invoice.total_price > amount:
            self.payment_repository.set_failed(failure_reason="Not enough money")
        else:
            invoice = self.payment_repository.set_paid(payment=invoice)
            user = invoice.user
            plan_metadata = invoice.get_metadata()
            plan_metadata.update({"promo_code": invoice.promo_code})
            self.user_repository.update_plan(
                user=user, plan_type_alias=invoice.plan, duration=invoice.duration, scope=invoice.scope, **plan_metadata
            )

        invoice_data = DetailInvoiceSerializer(invoice, many=False).data
        invoice_data["user_id"] = invoice.user_id
        return Response(status=200, data=invoice_data)

    @action(methods=["post"], detail=False)
    def referral_payment(self, request, *args, **kwargs):
        referral_user_ids = request.data.get("referral_user_ids", [])
        payment = Payment.objects.filter(
            status__in=[PAYMENT_STATUS_PAID], user_id__in=referral_user_ids
        )
        return Response(status=200, data={
            "count": payment.count()
        })
