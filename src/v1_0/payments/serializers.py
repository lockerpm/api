from django.forms import model_to_dict
from rest_framework import serializers

from core.settings import CORE_CONFIG
from shared.constants.transactions import *
from cystack_models.models.user_plans.pm_plans import PMPlan
from cystack_models.models.payments.payments import Payment
from cystack_models.models.payments.promo_codes import PromoCode


class CalcSerializer(serializers.Serializer):
    plan_alias = serializers.CharField()
    promo_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    duration = serializers.ChoiceField(choices=LIST_DURATION, default=DURATION_MONTHLY)
    number_members = serializers.IntegerField(default=1, min_value=1)
    currency = serializers.ChoiceField(
        choices=LIST_CURRENCY, default=CURRENCY_USD, required=False
    )

    def validate(self, data):
        # Validate plan alias
        plan_alias = data.get("plan_alias")
        try:
            plan = PMPlan.objects.exclude(alias=PLAN_TYPE_PM_FREE).get(alias=plan_alias)
            data["plan"] = plan
        except PMPlan.DoesNotExist:
            raise serializers.ValidationError(detail={"plan_alias": ["This plan alias does not exist"]})

        if plan.is_team_plan:
            if not data.get("number_members"):
                raise serializers.ValidationError(detail={"max_members": ["This field is required"]})
        else:
            data["number_members"] = 1

        return data


class FamilyMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(allow_null=True)
    email = serializers.EmailField()


class UpgradePlanSerializer(serializers.Serializer):
    plan_alias = serializers.CharField()
    promo_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    duration = serializers.ChoiceField(choices=LIST_DURATION, default=DURATION_MONTHLY, required=False)
    number_members = serializers.IntegerField(min_value=1, default=1)
    payment_method = serializers.ChoiceField(choices=LIST_PAYMENT_METHOD)
    bank_id = serializers.IntegerField(required=False)
    # Metadata for family plan
    family_members = FamilyMemberSerializer(many=True, required=False)
    # Metadata for team plans
    key = serializers.CharField(required=False, allow_null=True)
    collection_name = serializers.CharField(required=False, allow_null=True)

    def validate(self, data):
        current_user = self.context["request"].user
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        current_plan = user_repository.get_current_plan(user=current_user)

        # Validate plan
        plan_alias = data.get("plan_alias")
        try:
            plan = PMPlan.objects.get(alias=plan_alias)
            data["plan"] = plan
        except PMPlan.DoesNotExist:
            raise serializers.ValidationError(detail={'plan_alias': ["This plan does not exist"]})

        # Check number members of the plan
        if plan.is_team_plan:
            number_members = data.get("number_members")
            if not number_members:
                raise serializers.ValidationError(detail={"number_members": ["This field is required"]})
            max_allow_member = current_plan.get_max_allow_members()
            if max_allow_member and number_members < max_allow_member:
                raise serializers.ValidationError(detail={
                    "number_members": ["The minimum number of members is {}".format(max_allow_member)]
                })
        else:
            data["number_members"] = 1

        # Validate key and collection name of the team plan
        key = data.get("key")
        collection_name = data.get("collection_name")
        if plan.is_team_plan:
            if not key:
                raise serializers.ValidationError(detail={"key": ["This field is required"]})
            if not collection_name:
                raise serializers.ValidationError(detail={"collection_name": ["This field is required"]})

        # Check promo code
        promo_code = data.get("promo_code")
        if promo_code:
            promo_code_obj = PromoCode.check_valid(value=promo_code, current_user=current_user)
            if not promo_code_obj:
                raise serializers.ValidationError(detail={"promo_code": ["This coupon is expired or invalid"]})
            data["promo_code_obj"] = promo_code_obj

        # Check plan duration
        duration = data.get("duration")
        current_plan_alias = current_plan.get_plan_type_alias()
        if current_plan_alias == plan.get_alias() and current_plan.duration == duration:
            raise serializers.ValidationError(detail={"plan": ["Plan is not changed"]})

        # Check payment method
        payment_method = data.get("payment_method", PAYMENT_METHOD_CARD)
        current_payment_method = current_plan.get_default_payment_method()
        if current_plan_alias != PLAN_TYPE_PM_FREE and payment_method != current_payment_method:
            raise serializers.ValidationError(detail={
                "payment_method": ["This payment method must be same as current payment method of your plan"]
            })
        data["currency"] = CURRENCY_USD if payment_method == PAYMENT_METHOD_CARD else CURRENCY_VND

        # Check family members
        family_members = data.get("family_members", []) or []
        if plan.is_family_plan:
            if not family_members:
                raise serializers.ValidationError(detail={"members": ["The family members are required"]})
            if len(family_members) > plan.get_max_number_members() - 1:
                raise serializers.ValidationError(detail={
                    "members": ["The plan requires {} members including you".format(plan.get_max_number_members())]
                })
        else:
            data["family_members"] = []

        return data


class ListInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'payment_id', 'created_time', 'total_price', 'discount', 'status', 'description',
                  'transaction_type', 'payment_method', 'failure_reason', 'plan', 'duration', 'currency')
        read_only_field = ('id', 'created_time', 'total_price', 'discount', 'status',)

    def to_representation(self, instance):
        return super(ListInvoiceSerializer, self).to_representation(instance)


class DetailInvoiceSerializer(ListInvoiceSerializer):
    def to_representation(self, instance):
        data = super(DetailInvoiceSerializer, self).to_representation(instance)
        customer = instance.customer
        promo_code = instance.promo_code
        data["customer"] = model_to_dict(
            customer,
            fields=[field.name for field in customer._meta.fields if field.name != 'id']
        ) if customer is not None else None
        data["promo_code"] = promo_code.code if promo_code is not None else None
        data["code"] = instance.code
        data["bank_id"] = instance.bank_id

        return data
