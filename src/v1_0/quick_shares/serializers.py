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
    password = serializers.CharField(allow_null=True, required=False)
    max_access_count = serializers.IntegerField(min_value=0, allow_null=True, default=None)
    each_email_access_count = serializers.IntegerField(min_value=0, allow_null=True, default=None)
    expired_date = serializers.FloatField(min_value=0, required=False, allow_null=True)
    require_otp = serializers.BooleanField(default=True)
    emails = serializers.ListSerializer(
        child=serializers.EmailField(), allow_empty=True, required=False
    )

    def validate(self, data):
        each_email_access_count = data.get("each_email_access_count")
        emails = data.get("emails") or []
        emails_data = [{"email": email, "max_access_count": each_email_access_count} for email in emails]
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

        # Check the quick access is public or not
        data["is_public"] = True if not data.get("emails") else False

        return data

    def save(self, **kwargs):
        validated_data = self.validated_data
        # Cipher data
        validated_data["data"] = get_cipher_detail_data(validated_data)
        return validated_data

    def to_internal_value(self, data):
        return super().to_internal_value(data)


class ListQuickShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuickShare
        fields = ('access_id', 'creation_date', 'revision_date', 'deleted_date', 'key', 'password',
                  'max_access_count', 'access_count', 'each_email_access_count', 'expired_date', 'disabled',
                  'is_public', 'require_otp', )

    def to_representation(self, instance):
        result = super().to_representation(instance)
        data = instance.get_data()
        quick_share_data = data.copy()

        quick_share_data.pop("name", None)
        quick_share_data.pop("notes", None)
        fields = quick_share_data.get("fields")
        quick_share_data.pop("fields", None)

        login = quick_share_data if instance.type in [CIPHER_TYPE_LOGIN, CIPHER_TYPE_MASTER_PASSWORD] else None
        secure_note = quick_share_data if instance.type in [CIPHER_TYPE_NOTE, CIPHER_TYPE_TOTP] else None
        card = quick_share_data if instance.type == CIPHER_TYPE_CARD else None
        identity = quick_share_data if instance.type == CIPHER_TYPE_IDENTITY else None
        crypto_account = quick_share_data if instance.type == CIPHER_TYPE_CRYPTO_ACCOUNT else None
        crypto_wallet = quick_share_data if instance.type == CIPHER_TYPE_CRYPTO_WALLET else None
    
        result.update({
            "object": "quickShare",
            "id": instance.id,
            "card": card,
            "data": data,
            "fields": fields,
            "identity": identity,
            "login": login,
            "name": data.get("name"),
            "notes": data.get("notes"),
            "secure_note": secure_note,
            "crypto_account": crypto_account,
            "crypto_wallet": crypto_wallet,
            "revision_date": instance.revision_date,
            "type": instance.type,
        })
        return result


class DetailQuickShareSerializer(ListQuickShareSerializer):
    def to_representation(self, instance):
        data = super(DetailQuickShareSerializer, self).to_representation(instance)
        data["emails"] = instance.quick_share_emails.values('email', 'access_count', 'max_access_count')
        return data


class PublicQuickShareSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    code = serializers.CharField(max_length=128, required=False)


class CheckAccessQuickShareSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
