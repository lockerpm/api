from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from locker_server.api.api_base_view import APIBaseViewSet
from locker_server.api.permissions.micro_service_permissions.payment_permission import PaymentPermission
from locker_server.core.exceptions.payment_exception import PaymentInvoiceDoesNotExistException
from locker_server.api.v1_0.payments.serializers import DetailInvoiceSerializer
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.shared.constants.transactions import *
from .serializers import InvoiceWebhookSerializer, PaymentStatusWebhookSerializer, BankingCallbackSerializer


class PaymentViewSet(APIBaseViewSet):
    permission_classes = (PaymentPermission, )
    http_method_names = ["head", "options", "post", "put"]

    def get_serializer_class(self):
        if self.action == "webhook_create":
            self.serializer_class = InvoiceWebhookSerializer
        elif self.action in ["webhook_set_status", "charge_set_status"]:
            self.serializer_class = PaymentStatusWebhookSerializer
        elif self.action == "banking_callback":
            self.serializer_class = BankingCallbackSerializer
        return super().get_serializer_class()

    @action(methods=["post"], detail=False)
    def charge_set_status(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK, data={"success": True})

    @action(methods=["post"], detail=False)
    def webhook_create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        result = self.payment_hook_service.webhook_create(**validated_data)
        new_payment = result.get("new_payment")
        payment_data = result.get("payment_data", {})
        subtotal = new_payment.total_price + new_payment.discount
        if payment_data.get("enterprise_id") and new_payment.plan == PLAN_TYPE_PM_ENTERPRISE:
            enterprise_billing_contacts = self.payment_hook_service.list_enterprise_billing_emails(
                enterprise_id=payment_data.get("enterprise_id")
            )
        else:
            enterprise_billing_contacts = []
        return Response(status=status.HTTP_200_OK, data={
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
            "payment_data": payment_data,
            "cc": enterprise_billing_contacts
        })

    @action(methods=["post"], detail=False)
    def webhook_set_status(self, request, *args, **kwargs):
        invoice_id = kwargs.get("pk")
        try:
            payment = self.payment_service.get_by_payment_id(payment_id=invoice_id)
        except PaymentInvoiceDoesNotExistException:
            raise NotFound
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        payment_status = validated_data.get("status")
        failure_reason = validated_data.get("failure_reason")
        payment_data = self.payment_hook_service.webhook_set_status(
            payment=payment, payment_status=payment_status, failure_reason=failure_reason,
            locker_web_url=settings.LOCKER_WEB_URL
        )
        return Response(status=200, data=payment_data)

    @action(methods=["post"], detail=False)
    def webhook_unpaid_subscription(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        scope = self.request.query_params.get("scope", settings.SCOPE_PWD_MANAGER)
        try:
            user = self.user_service.retrieve_by_id(user_id=user_id)
        except (ValueError, UserDoesNotExistException):
            raise NotFound
        self.payment_hook_service.webhook_unpaid_subscription(user=user)
        return Response(status=status.HTTP_200_OK, data={"user_id": user_id})

    @action(methods=["put"], detail=False)
    def webhook_cancel_subscription(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        scope = self.request.query_params.get("scope", settings.SCOPE_PWD_MANAGER)
        try:
            user = self.user_service.retrieve_by_id(user_id=user_id)
        except (ValueError, UserDoesNotExistException):
            raise NotFound

        old_plan = self.payment_hook_service.webhook_cancel_subscription(
            user=user, plan=request.data.get("plan"), scope=scope
        )
        return Response(status=status.HTTP_200_OK, data={"old_plan": old_plan})

    @action(methods=["post"], detail=False)
    def banking_callback(self, request, *arg, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        amount = validated_data.get("amount")
        code = validated_data.get("code")
        try:
            invoice = self.payment_hook_service.banking_callback(
                code=code, amount=amount
            )
        except PaymentInvoiceDoesNotExistException:
            raise NotFound

        invoice_data = DetailInvoiceSerializer(invoice, many=False).data
        invoice_data["user_id"] = invoice.user_id
        return Response(status=200, data=invoice_data)

    @action(methods=["post"], detail=False)
    def referral_payment(self, request, *args, **kwargs):
        referral_user_ids = request.data.get("referral_user_ids", [])
        return Response(status=status.HTTP_200_OK, data={
            "count": self.payment_hook_service.count_referral_payment(referral_user_ids=referral_user_ids)
        })
