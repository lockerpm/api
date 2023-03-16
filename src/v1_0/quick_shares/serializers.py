from rest_framework import serializers

from core.settings import CORE_CONFIG
from cystack_models.models.quick_shares.quick_shares import QuickShare
from shared.constants.ciphers import *
from shared.constants.transactions import PLAN_TYPE_PM_FREE
from shared.error_responses.error import gen_error
from shared.utils.app import get_cipher_detail_data
from v1_0.ciphers.serializers import ItemFieldSerializer, LoginVaultSerializer, SecurityNoteVaultSerializer, \
    CardVaultSerializer, IdentityVaultSerializer, CryptoAccountSerializer, CryptoWalletSerializer


class CreateQuickShareSerializer(serializers.Serializer):
    cipher_id = serializers.CharField(max_length=128)
    fields = ItemFieldSerializer(many=True, required=False, allow_null=True)
    name = serializers.CharField()
    notes = serializers.CharField(allow_blank=True, allow_null=True)
    type = serializers.ChoiceField(choices=LIST_CIPHER_TYPE)
    login = LoginVaultSerializer(required=False, many=False, allow_null=True)
    secureNote = SecurityNoteVaultSerializer(required=False, many=False, allow_null=True)
    card = CardVaultSerializer(required=False, many=False, allow_null=True)
    identity = IdentityVaultSerializer(required=False, many=False, allow_null=True)
    cryptoAccount = CryptoAccountSerializer(required=False, many=False, allow_null=True)
    cryptoWallet = CryptoWalletSerializer(required=False, many=False, allow_null=True)

    key = serializers.CharField()
    password = serializers.CharField()
    max_access_count = serializers.IntegerField(min_value=0, allow_null=True)
    expired_date = serializers.FloatField(min_value=0, required=False, allow_null=True)
    require_otp = serializers.BooleanField(default=True)
    emails = serializers.ListSerializer(
        child=serializers.EmailField(), allow_empty=True, required=False
    )

    def validate(self, data):
        emails = data.get("emails") or []
        emails_data = [{"email": email} for email in emails]
        data["emails"] = emails_data

        # Validate vault data
        vault_type = data.get("type")
        login = data.get("login", {})
        secure_note = data.get("secureNote")
        card = data.get("card")
        identity = data.get("identity")
        if vault_type == CIPHER_TYPE_LOGIN and not login:
            raise serializers.ValidationError(detail={"login": ["This field is required"]})
        if vault_type == CIPHER_TYPE_NOTE and not secure_note:
            raise serializers.ValidationError(detail={"secureNote": ["This field is required"]})
        if vault_type == CIPHER_TYPE_CARD and not card:
            raise serializers.ValidationError(detail={"card": ["This field is required"]})
        if vault_type == CIPHER_TYPE_IDENTITY and not identity:
            raise serializers.ValidationError(detail={"identity": ["This field is required"]})

        return data

    def save(self, **kwargs):
        validated_data = self.validated_data
        check_plan = kwargs.get("check_plan", False)
        if check_plan is True:
            validated_data = self.validated_plan(validated_data)

        cipher_type = validated_data.get("type")
        detail = {
            "edit": True,
            "type": cipher_type,
            "fields": validated_data.get("fields"),
        }
        # Cipher data
        detail.update({"data": get_cipher_detail_data(validated_data)})

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
            data["is_public"] = True
        else:
            data["is_public"] = False
        return super().to_internal_value(data)


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
