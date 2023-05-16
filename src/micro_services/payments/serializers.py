import stripe

from django.conf import settings
from rest_framework import serializers

from core.settings import CORE_CONFIG
from shared.constants.transactions import *
from cystack_models.models.payments.payments import Payment
from shared.utils.app import now


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

    def save(self, **kwargs):
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        payment_repository = CORE_CONFIG["repositories"]["IPaymentRepository"]()

        # Check this invoice with stripe_invoice_id existed                                           ?
        stripe_invoice_exist = False
        stripe_subscription_obj = None
        stripe_card_id = None
        # Get validated data
        validated_data = self.validated_data
        scope = validated_data.get("scope")
        stripe_subscription_id = validated_data.get("stripe_subscription_id")
        stripe_invoice_id = validated_data.get("stripe_invoice_id", None)
        if stripe_invoice_id is not None:
            stripe_invoice_exist = Payment.objects.filter(stripe_invoice_id=stripe_invoice_id).exists()
        if stripe_subscription_id:
            stripe_subscription_obj = stripe.Subscription.retrieve(stripe_subscription_id)
            stripe_card_id = stripe_subscription_obj.default_payment_method

        # If we dont have a payment with stripe_invoice_id => Create new one
        if stripe_invoice_exist is False:
            user = user_repository.retrieve_or_create_by_id(user_id=validated_data["user_id"])
            validated_data["user"] = user
            validated_data["customer"] = user_repository.get_customer_data(user=user, id_card=stripe_card_id)
            validated_data["duration"] = validated_data.get("duration", DURATION_MONTHLY)
            validated_data["metadata"] = stripe_subscription_obj.get("metadata", {}) if stripe_subscription_obj else {}
            promo_code = validated_data.get("promo_code")
            if promo_code:
                promo_code_id = promo_code.replace("_half_yearly", "").replace("_yearly", "").replace("_monthly", "")
                validated_data["promo_code"] = promo_code_id
            # Find payments items
            payments_items = []
            validated_data["payments_items"] = payments_items

            # Create new payment
            new_payment = Payment.create(**validated_data)

            # Set total amount
            if validated_data.get("total") is not None:
                new_payment.total_price = round(float(validated_data.get("total") / 100), 2)
                new_payment.discount = round(float(
                    (validated_data.get("subtotal") - validated_data.get("total")) / 100
                ), 2)
                if new_payment.total_price < 0:
                    new_payment.transaction_type = TRANSACTION_TYPE_REFUND
                    new_payment.total_price = -new_payment.total_price
                new_payment.save()
        # Else, retrieving the payment with stripe_payment_id
        else:
            new_payment = Payment.objects.filter(stripe_invoice_id=stripe_invoice_id).first()

        result = {}
        paid = validated_data.get("paid")
        extra_time = 0
        extra_plan = None
        if paid is True:
            new_payment = payment_repository.set_paid(payment=new_payment)
            if stripe_subscription_obj:
                pm_user_plan = user_repository.get_current_plan(user=new_payment.user, scope=scope)
                # if this user is in a trial plan => Set extra time
                if pm_user_plan.end_period and pm_user_plan.pm_stripe_subscription is None:
                    extra_time = max(pm_user_plan.end_period - now(), 0)
                    extra_plan = pm_user_plan.get_plan_obj().get_alias()

                pm_user_plan.pm_stripe_subscription = stripe_subscription_id
                pm_user_plan.pm_stripe_subscription_created_time = now()
                if stripe_subscription_obj.status == "trialing":
                    pm_user_plan.personal_trial_applied = True
                    pm_user_plan.personal_trial_web_applied = True
                pm_user_plan.save()

                start_period = stripe_subscription_obj.current_period_start
                end_period = stripe_subscription_obj.current_period_end

                # Upgrade the plan of this user
                subscription_metadata = {
                    "start_period": start_period,
                    "end_period": end_period,
                    "promo_code": new_payment.promo_code,
                    "family_members": stripe_subscription_obj.get("metadata", {}).get("family_members", []),
                    "extra_time": extra_time,
                    "extra_plan": extra_plan
                }
                updated_user_plan = user_repository.update_plan(
                    new_payment.user, plan_type_alias=new_payment.plan, duration=new_payment.duration, scope=scope,
                    **subscription_metadata
                )
                enterprise = user_repository.get_default_enterprise(user=new_payment.user)
                result["payment_data"] = {
                    "enterprise_id": enterprise.id if enterprise else None,
                    "enterprise_name": enterprise.name if enterprise else None,
                    "stripe_invoice_id": new_payment.stripe_invoice_id,
                    "plan_name": updated_user_plan.get_plan_type_name(),
                    "plan_price": updated_user_plan.pm_plan.get_price(
                        currency=new_payment.currency, duration=new_payment.duration
                    ),
                    "number_members": int(new_payment.get_metadata().get("number_members", 1)) or 1,
                    "start_period": start_period,
                    "end_period": end_period,
                }

        else:
            new_payment = payment_repository.set_failed(new_payment, failure_reason=validated_data.get("failure_reason"))

        result["new_payment"] = new_payment
        return result


class PaymentStatusWebhookSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[PAYMENT_STATUS_FAILED, PAYMENT_STATUS_PAST_DUE, PAYMENT_STATUS_PAID])
    failure_reason = serializers.CharField(required=False, allow_blank=True)


class BankingCallbackSerializer(serializers.Serializer):
    amount = serializers.FloatField()
    code = serializers.CharField(max_length=128)
