from django.conf import settings
from rest_framework import serializers

from cystack_models.models.users.users import User
from cystack_models.models.payments.payments import Payment
from shared.constants.transactions import *
from shared.utils.app import now


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
    # total = serializers.FloatField(required=False)
    # subtotal = serializers.FloatField(required=False)
    platform = serializers.ChoiceField(choices=["ios", "android"])
    mobile_transaction_id = serializers.CharField(required=False, allow_null=True)
    mobile_original_id = serializers.CharField(required=False, allow_null=True)
    currency = serializers.CharField(required=False, default=CURRENCY_USD)
    failure_reason = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)

    def validate(self, data):
        user_id = data.get("user_id")
        try:
            user = User.objects.get(user_id=user_id)
            data["user"] = user
        except User.DoesNotExist:
            raise serializers.ValidationError(detail={"user_id": ["User does not exist"]})

        return data

