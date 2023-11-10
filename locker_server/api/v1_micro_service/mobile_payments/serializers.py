from rest_framework import serializers

from locker_server.shared.constants.transactions import *


class FamilyMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(allow_null=True)
    email = serializers.EmailField()


class UpgradePlanSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    family_members = FamilyMemberSerializer(many=True, required=False)
    description = serializers.CharField(allow_blank=True, default="")
    promo_code = serializers.CharField(required=False, allow_null=True)
    paid = serializers.BooleanField(default=True)
    duration = serializers.ChoiceField(choices=LIST_DURATION, required=False, default=DURATION_MONTHLY)
    plan = serializers.CharField()
    platform = serializers.ChoiceField(choices=["ios", "android"])
    mobile_invoice_id = serializers.CharField(required=False, allow_null=True)
    mobile_original_id = serializers.CharField(required=False, allow_null=True)
    confirm_original_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    currency = serializers.CharField(required=False, default=CURRENCY_USD)
    failure_reason = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    end_period = serializers.FloatField(required=False, allow_null=True)
    is_trial_period = serializers.BooleanField(default=False)


class MobileRenewalSerializer(serializers.Serializer):
    description = serializers.CharField(allow_blank=True, default="")
    promo_code = serializers.CharField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=[PAYMENT_STATUS_PAID, PAYMENT_STATUS_FAILED, PAYMENT_STATUS_PAST_DUE], default=PAYMENT_STATUS_PAID
    )
    duration = serializers.ChoiceField(choices=LIST_DURATION, required=False, default=DURATION_MONTHLY)
    plan = serializers.CharField()
    platform = serializers.ChoiceField(choices=["ios", "android"])
    mobile_invoice_id = serializers.CharField(required=False, allow_null=True)
    mobile_original_id = serializers.CharField()
    currency = serializers.CharField(required=False, default=CURRENCY_USD)
    failure_reason = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    end_period = serializers.FloatField(required=False, allow_null=True)


class MobileCancelSubscriptionSerializer(serializers.Serializer):
    mobile_original_id = serializers.CharField()
    cancel_at_period_end = serializers.BooleanField()
    end_period = serializers.FloatField(required=False, allow_null=True)


class MobileDestroySubscriptionSerializer(serializers.Serializer):
    mobile_original_id = serializers.CharField()

    # def validate(self, data):
    #     mobile_original_id = data.get("mobile_original_id")
    #     user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
    #     user_plan = user_repository.get_mobile_user_plan(pm_mobile_subscription=mobile_original_id)
    #     if not user_plan:
    #         raise serializers.ValidationError(detail={
    #             "mobile_original_id": ["The mobile subscription id {} does not exist".format(mobile_original_id)]
    #         })
    #     data["user"] = user_plan.user
    #     return data
