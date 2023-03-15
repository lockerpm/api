from rest_framework import serializers

from core.settings import CORE_CONFIG
from cystack_models.models.quick_shares.quick_shares import QuickShare
from shared.constants.transactions import PLAN_TYPE_PM_FREE
from shared.error_responses.error import gen_error


class CreateQuickShareSerializer(serializers.Serializer):
    cipher_id = serializers.CharField(max_length=128)
    data = serializers.CharField()
    key = serializers.CharField()
    password = serializers.CharField()
    max_access_count = serializers.IntegerField(min_value=0, allow_null=True)
    expired_date = serializers.FloatField(min_value=0, required=False, allow_null=True)
    is_public = serializers.BooleanField(default=True)
    require_otp = serializers.BooleanField(default=False)
    emails = serializers.ListSerializer(
        child=serializers.EmailField(), allow_empty=True, required=False
    )

    def validate(self, data):
        emails = data.get("emails") or []
        emails_data = [{"email": email} for email in emails]
        data["emails"] = emails_data
        return data

    def save(self, **kwargs):
        validated_data = self.validated_data
        check_plan = kwargs.get("check_plan", False)
        if check_plan is True:
            validated_data = self.validated_plan(validated_data)
        return validated_data

    def validated_plan(self, data):
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        user = self.context["request"].user
        current_plan = user_repository.get_current_plan(user=user)
        # TODO: Check the plan of the user
        # if current_plan.get_plan_type_alias() == PLAN_TYPE_PM_FREE:
        #     raise serializers.ValidationError(detail={"non_field_errors": [gen_error("7002")]})



        return data

    def to_internal_value(self, data):
        if not data.get("emails"):
            data["emails"] = []
        return super().to_internal_value(data)


class ListQuickShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuickShare
        fields = ('access_id', 'creation_date', 'revision_date', 'deleted_date', 'data', 'key', 'password',
                  'max_access_count', 'access_count', 'expired_date', 'disable', 'is_public', 'require_otp', )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["id"] = instance.cipher_id
        return data
