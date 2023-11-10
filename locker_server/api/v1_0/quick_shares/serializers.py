from rest_framework import serializers


from locker_server.api.v1_0.ciphers.serializers import ItemFieldSerializer, LoginVaultSerializer, \
    SecurityNoteVaultSerializer, CardVaultSerializer, IdentityVaultSerializer, CryptoAccountSerializer, \
    CryptoWalletSerializer
from locker_server.shared.constants.ciphers import *
from locker_server.shared.utils.app import get_cipher_detail_data, convert_readable_date


class CipherQuickShareSerializer(serializers.Serializer):
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

    def validate(self, data):
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
        # Cipher data
        validated_data["data"] = get_cipher_detail_data(validated_data)
        return validated_data

    def to_internal_value(self, data):
        return super().to_internal_value(data)


class CreateQuickShareSerializer(serializers.Serializer):
    cipher_id = serializers.CharField(max_length=128)
    cipher = CipherQuickShareSerializer(many=False, required=True)
    key = serializers.CharField()
    password = serializers.CharField(allow_null=True, required=False)
    max_access_count = serializers.IntegerField(min_value=0, allow_null=True, default=None)
    each_email_access_count = serializers.IntegerField(min_value=0, allow_null=True, default=None)
    expiration_date = serializers.FloatField(min_value=0, required=False, allow_null=True)
    require_otp = serializers.BooleanField(default=True)
    emails = serializers.ListSerializer(
        child=serializers.EmailField(), allow_empty=True, required=False
    )

    def validate(self, data):
        each_email_access_count = data.get("each_email_access_count")
        emails = data.get("emails") or []
        emails_data = [{"email": email, "max_access_count": each_email_access_count} for email in emails]
        data["emails"] = emails_data
        data["is_public"] = True if not data.get("emails") else False

        return data

    def save(self, **kwargs):
        validated_data = self.validated_data
        # Cipher data
        cipher = validated_data.get("cipher")
        validated_data["data"] = get_cipher_detail_data(cipher)
        validated_data["type"] = cipher.get("type")
        return validated_data

    def to_internal_value(self, data):
        return super().to_internal_value(data)


class ListQuickShareSerializer(serializers.Serializer):

    def to_representation(self, instance):
        data = instance.data
        quick_share_data = data.copy()
        quick_share_data.pop("name", None)
        quick_share_data.pop("notes", None)
        fields = quick_share_data.get("fields")
        quick_share_data.pop("fields", None)

        login = quick_share_data if instance.quick_share_type in [CIPHER_TYPE_LOGIN, CIPHER_TYPE_MASTER_PASSWORD] else None
        secure_note = quick_share_data if instance.quick_share_type in [CIPHER_TYPE_NOTE, CIPHER_TYPE_TOTP] else None
        card = quick_share_data if instance.quick_share_type == CIPHER_TYPE_CARD else None
        identity = quick_share_data if instance.quick_share_type == CIPHER_TYPE_IDENTITY else None
        crypto_account = quick_share_data if instance.quick_share_type == CIPHER_TYPE_CRYPTO_ACCOUNT else None
        crypto_wallet = quick_share_data if instance.quick_share_type == CIPHER_TYPE_CRYPTO_WALLET else None

        result = {
            "object": "quickShare",
            "id": instance.quick_share_id,
            "cipher_id": instance.cipher.cipher_id,
            "cipher": {
                "type": instance.quick_share_type,
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
            },
            "creation_date": convert_readable_date(instance.creation_date),
            "revision_date": convert_readable_date(instance.revision_date),
            "deleted_date": convert_readable_date(instance.deleted_date),
            "expiration_date": convert_readable_date(instance.expiration_date),
            "access_id": instance.access_id,
            "key": instance.key,
            "password": instance.password,
            "max_access_count": instance.max_access_count,
            "access_count": instance.access_count,
            "each_email_access_count": instance.each_email_access_count,
            "disabled": instance.disabled,
            "is_public": instance.is_public,
            "require_otp": instance.require_otp,
            "emails": instance.emails,
        }
        return result


class DetailQuickShareSerializer(ListQuickShareSerializer):
    def to_representation(self, instance):
        data = super(DetailQuickShareSerializer, self).to_representation(instance)
        return data


class PublicAccessQuickShareSerializer(ListQuickShareSerializer):
    def to_representation(self, instance):
        data = super(PublicAccessQuickShareSerializer, self).to_representation(instance)
        public_data = {
            "id": data.get("id"),
            "cipher": data.get("cipher")
        }
        return public_data


class PublicQuickShareSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    code = serializers.CharField(max_length=128, required=False)
    token = serializers.CharField(max_length=512, required=False)


class CheckAccessQuickShareSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
