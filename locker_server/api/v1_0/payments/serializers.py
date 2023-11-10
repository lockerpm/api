from django.forms import model_to_dict
from rest_framework import serializers

from locker_server.shared.constants.transactions import *
from locker_server.shared.utils.app import now


class FamilyMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(allow_null=True)
    email = serializers.EmailField()


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
        if plan_alias == PLAN_TYPE_PM_FREE:
            raise serializers.ValidationError(detail={"plan_alias": ["This plan alias does not exist"]})
        return data


class UpgradePlanSerializer(serializers.Serializer):
    plan_alias = serializers.ChoiceField(choices=[PLAN_TYPE_PM_FREE, PLAN_TYPE_PM_PREMIUM, PLAN_TYPE_PM_FAMILY])
    promo_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    duration = serializers.ChoiceField(choices=LIST_DURATION, default=DURATION_MONTHLY, required=False)
    number_members = serializers.IntegerField(min_value=1, default=1)
    payment_method = serializers.ChoiceField(choices=LIST_PAYMENT_METHOD)
    bank_id = serializers.IntegerField(required=False)
    # Metadata for family plan
    family_members = FamilyMemberSerializer(many=True, required=False)

    def validate(self, data):
        data["number_members"] = 1
        # Check payment method
        payment_method = data.get("payment_method", PAYMENT_METHOD_CARD)
        data["currency"] = CURRENCY_USD if payment_method == PAYMENT_METHOD_CARD else CURRENCY_VND
        return data


class ListInvoiceSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.id,
            "payment_id": instance.payment_id,
            "created_time": instance.created_time,
            "total_price": instance.total_price,
            "discount": instance.discount,
            "status": instance.status,
            "description": instance.description,
            "transaction_type": instance.transaction_type,
            "payment_method": instance.payment_method,
            "failure_reason": instance.failure_reason,
            "plan": instance.plan,
            "duration": instance.duration,
            "currency": instance.currency
        }
        return data


class DetailInvoiceSerializer(ListInvoiceSerializer):
    def to_representation(self, instance):
        data = super(DetailInvoiceSerializer, self).to_representation(instance)
        customer = instance.customer
        promo_code = instance.promo_code
        data["customer"] = model_to_dict(
            customer,
            fields=[field.name for field in customer._meta.fields if field.name != 'id' and field.name != 'customer_id']
        ) if customer is not None else None
        data["promo_code"] = promo_code.code if promo_code is not None else None
        data["code"] = instance.code
        data["bank_id"] = instance.bank_id

        return data


class AdminUpgradePlanSerializer(serializers.Serializer):
    plan_alias = serializers.CharField()
    end_period = serializers.IntegerField(allow_null=True)

    def validate(self, data):
        # Validate plan
        plan_alias = data.get("plan_alias")
        end_period = data.get("end_period")
        if plan_alias == PLAN_TYPE_PM_FREE:
            data["end_period"] = None
        else:
            data["end_period"] = end_period or now() + 30 * 86400

        return data


class UpgradeTrialSerializer(serializers.Serializer):
    trial_plan = serializers.ChoiceField(choices=[PLAN_TYPE_PM_PREMIUM, PLAN_TYPE_PM_FAMILY])


class UpgradeLifetimeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=32)


class UpgradeThreePromoSerializer(serializers.Serializer):
    promo_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class CalcLifetimePublicSerializer(serializers.Serializer):
    promo_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    currency = serializers.ChoiceField(choices=LIST_CURRENCY, default=CURRENCY_USD, required=False)
    plan_alias = serializers.ChoiceField(
        choices=[PLAN_TYPE_PM_LIFETIME, PLAN_TYPE_PM_LIFETIME_FAMILY], default=PLAN_TYPE_PM_LIFETIME,
        required=False
    )
    email = serializers.EmailField(required=False, allow_null=True)


class UpgradeLifetimePublicSerializer(serializers.Serializer):
    promo_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    plan_alias = serializers.ChoiceField(
        choices=[PLAN_TYPE_PM_LIFETIME, PLAN_TYPE_PM_LIFETIME_FAMILY], default=PLAN_TYPE_PM_LIFETIME,
        required=False
    )


class UpgradeEducationPublicSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=128)
    education_email = serializers.EmailField(max_length=255, required=False, allow_blank=True, allow_null=True)
    education_type = serializers.ChoiceField(choices=["teacher", "student"], default="student")
    university = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)

    def to_internal_value(self, data):
        if data.get("education_email") is None:
            data["education_email"] = ""
        if data.get("university") is None:
            data["university"] = ""
        return super().to_internal_value(data)


class CancelPlanSerializer(serializers.Serializer):
    immediately = serializers.BooleanField(default=False)

