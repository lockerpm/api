from rest_framework import serializers

from core.settings import CORE_CONFIG
from cystack_models.models.payments.promo_codes import PromoCode
from cystack_models.models.payments.payments import Payment
from cystack_models.models.user_plans.pm_plans import PMPlan
from shared.constants.transactions import *


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'payment_id', 'created_time', 'total_price', 'discount', 'status', 'payment_method',
                  'duration', 'currency')
        read_only_field = ('id', 'created_time', 'total_price', 'discount', 'status', 'payment_method',
                           'duration', 'currency', )

    def to_representation(self, instance):
        return super(InvoiceSerializer, self).to_representation(instance)


class CalcSerializer(serializers.Serializer):
    promo_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    duration = serializers.ChoiceField(choices=LIST_DURATION, default=DURATION_MONTHLY)
    currency = serializers.ChoiceField(choices=LIST_CURRENCY, default=CURRENCY_USD, required=False)


class UpgradePlanSerializer(serializers.Serializer):
    promo_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    duration = serializers.ChoiceField(choices=LIST_DURATION, default=DURATION_MONTHLY, required=False)

    def validate(self, data):
        current_user = self.context["request"].user
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        current_plan = user_repository.get_current_plan(user=current_user)

        plan = PMPlan.objects.get(alias=PLAN_TYPE_PM_ENTERPRISE)
        data["plan"] = plan

        promo_code = data.get("promo_code")
        if promo_code:
            promo_code_obj = PromoCode.check_valid(value=promo_code, current_user=current_user)
            if not promo_code_obj:
                raise serializers.ValidationError(detail={"promo_code": ["This coupon is expired or invalid"]})
            data["promo_code_obj"] = promo_code_obj

        # Check plan duration
        # duration = data.get("duration")
        # current_plan_alias = current_plan.get_plan_type_alias()
        # if current_plan_alias == plan.get_alias() and current_plan.duration == duration:
        #     raise serializers.ValidationError(detail={"plan": ["Plan is not changed"]})

        data["currency"] = CURRENCY_USD

        return data
