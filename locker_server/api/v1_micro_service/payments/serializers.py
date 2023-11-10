from django.conf import settings
from rest_framework import serializers

from locker_server.shared.constants.transactions import *


class InvoiceWebhookSerializer(serializers.Serializer):
    """
    This is serializer class for creating or retrieving payment by Stripe webhook
    """
    description = serializers.CharField(allow_blank=True)
    user_id = serializers.IntegerField()
    scope = serializers.ChoiceField(choices=[settings.SCOPE_PWD_MANAGER])
    promo_code = serializers.CharField(required=False, allow_null=True)
    paid = serializers.BooleanField()
    duration = serializers.CharField(required=False, default=DURATION_MONTHLY)
    total = serializers.FloatField(required=False)
    subtotal = serializers.FloatField(required=False)
    stripe_invoice_id = serializers.CharField(required=False)
    stripe_subscription_id = serializers.CharField(required=True)
    failure_reason = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    currency = serializers.CharField(required=False, default=CURRENCY_USD)
    plan = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class PaymentStatusWebhookSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[PAYMENT_STATUS_FAILED, PAYMENT_STATUS_PAST_DUE, PAYMENT_STATUS_PAID])
    failure_reason = serializers.CharField(required=False, allow_blank=True)


class BankingCallbackSerializer(serializers.Serializer):
    amount = serializers.FloatField()
    code = serializers.CharField(max_length=128)

