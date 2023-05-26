from django.forms import model_to_dict
from rest_framework import serializers

from core.settings import CORE_CONFIG
from cystack_models.models.payments.promo_codes import PromoCode
from cystack_models.models.payments.payments import Payment
from cystack_models.models.user_plans.pm_plans import PMPlan
from cystack_models.models.payments.country import Country
from cystack_models.models.enterprises.enterprises import Enterprise
from shared.constants.transactions import *
from shared.utils.app import now


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'payment_id', 'created_time', 'total_price', 'discount', 'status', 'payment_method',
                  'duration', 'currency', 'plan', )
        read_only_field = ('id', 'created_time', 'total_price', 'discount', 'status', 'payment_method',
                           'duration', 'currency', 'plan', )

    def to_representation(self, instance):
        return super(InvoiceSerializer, self).to_representation(instance)


class DetailInvoiceSerializer(InvoiceSerializer):
    def to_representation(self, instance):
        data = super(DetailInvoiceSerializer, self).to_representation(instance)
        customer = instance.customer
        promo_code = instance.promo_code
        data["customer"] = model_to_dict(
            customer,
            fields=[field.name for field in customer._meta.fields if field.name != 'id']
        ) if customer is not None else None
        data["promo_code"] = promo_code.code if promo_code is not None else None

        return data


class CalcSerializer(serializers.Serializer):
    promo_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    duration = serializers.ChoiceField(choices=LIST_DURATION, default=DURATION_MONTHLY)
    currency = serializers.ChoiceField(choices=LIST_CURRENCY, default=CURRENCY_USD, required=False)


class CalcPublicSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=True, min_value=1)
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
        duration = data.get("duration")
        if promo_code:
            promo_code_obj = PromoCode.check_valid(value=promo_code, current_user=current_user, new_duration=duration)
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


class UpgradePlanPublicSerializer(UpgradePlanSerializer):
    quantity = serializers.IntegerField(min_value=1, default=1)
    organization = serializers.CharField(max_length=128, default="My Enterprise")
    enterprise_address1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    enterprise_address2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    enterprise_phone = serializers.CharField(max_length=128, required=False, allow_blank=True)
    enterprise_country = serializers.CharField(max_length=128, required=False, allow_blank=True)
    enterprise_postal_code = serializers.CharField(max_length=16, required=False, allow_blank=True)



class BillingAddressSerializer(serializers.ModelSerializer):
    enterprise_name = serializers.CharField(max_length=128, required=False, allow_blank=True)
    enterprise_address1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    enterprise_address2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    enterprise_phone = serializers.CharField(max_length=128, required=False, allow_blank=True)
    enterprise_country = serializers.CharField(max_length=128, required=False, allow_blank=True)
    enterprise_postal_code = serializers.CharField(max_length=16, required=False, allow_blank=True)

    class Meta:
        model = Enterprise
        fields = ('id', 'enterprise_name', 'enterprise_address1', 'enterprise_address2', 'enterprise_phone',
                  'enterprise_country', 'enterprise_postal_code')
        read_only_fields = ('id', )

    def validate(self, data):
        enterprise_country = data.get("enterprise_country")
        if enterprise_country and Country.objects.filter(country_code=enterprise_country).exists() is False:
            raise serializers.ValidationError(detail={"enterprise_country": ["The country does not exist"]})

        return data

    def update(self, instance, validated_data):
        instance.enterprise_name = validated_data.get("enterprise_name", instance.enterprise_name)
        instance.enterprise_address1 = validated_data.get("enterprise_address1", instance.enterprise_address1)
        instance.enterprise_address2 = validated_data.get("enterprise_address2", instance.enterprise_address2)
        instance.enterprise_phone = validated_data.get("enterprise_phone", instance.enterprise_phone)
        instance.enterprise_country = validated_data.get("enterprise_country", instance.enterprise_country)
        instance.enterprise_postal_code = validated_data.get("enterprise_postal_code", instance.enterprise_postal_code)
        instance.revision_date = now()
        instance.save()
        return instance

