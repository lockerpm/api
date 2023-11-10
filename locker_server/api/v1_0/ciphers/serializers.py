from rest_framework import serializers

from locker_server.api.v1_0.folders.serializers import FolderSerializer
from locker_server.api.v1_0.sync.serializers import SyncCipherSerializer
from locker_server.shared.constants.ciphers import *
from locker_server.shared.error_responses.error import gen_error
from locker_server.shared.utils.app import get_cipher_detail_data


class ItemFieldSerializer(serializers.Serializer):
    name = serializers.CharField(allow_blank=True, allow_null=True)
    response = serializers.CharField(required=False, allow_null=True, default=None)
    type = serializers.ChoiceField(choices=LIST_CUSTOM_FIELD_TYPE)
    value = serializers.CharField(allow_blank=True, allow_null=True)


class LoginUriVaultSerializer(serializers.Serializer):
    match = serializers.CharField(required=False, allow_null=True, default=None)
    response = serializers.CharField(required=False, allow_null=True, default=None)
    uri = serializers.CharField(allow_null=True)


class LoginVaultSerializer(serializers.Serializer):
    autofillOnPageLoad = serializers.BooleanField(required=False, allow_null=True, default=None)
    username = serializers.CharField(allow_null=True, allow_blank=True)
    password = serializers.CharField(allow_null=True, allow_blank=True)
    totp = serializers.CharField(allow_null=True, allow_blank=True)
    response = serializers.CharField(allow_null=True, allow_blank=True, default=None)
    uris = LoginUriVaultSerializer(many=True, allow_null=True)


class CryptoAccountSerializer(serializers.Serializer):
    username = serializers.CharField(allow_null=True, allow_blank=True)
    password = serializers.CharField(allow_null=True, allow_blank=True)
    phone = serializers.CharField(allow_null=True, allow_blank=True)
    emailRecovery = serializers.CharField(allow_null=True, allow_blank=True)
    response = serializers.CharField(allow_null=True, allow_blank=True, default=None)
    uris = LoginUriVaultSerializer(many=True, allow_null=True)


class CryptoWalletSerializer(serializers.Serializer):
    email = serializers.CharField(allow_null=True, allow_blank=True)
    seed = serializers.CharField(allow_null=True, allow_blank=True)


class CardVaultSerializer(serializers.Serializer):
    brand = serializers.CharField(allow_null=True, allow_blank=True)
    cardholderName = serializers.CharField(allow_null=True, allow_blank=True)
    code = serializers.CharField(allow_null=True, allow_blank=True)
    expMonth = serializers.CharField(allow_null=True, allow_blank=True)
    expYear = serializers.CharField(allow_null=True, allow_blank=True)
    number = serializers.CharField(allow_null=True, allow_blank=True)
    response = serializers.CharField(allow_null=True, allow_blank=True, default=None)


class IdentityVaultSerializer(serializers.Serializer):
    address1 = serializers.CharField(allow_null=True, allow_blank=True)
    address2 = serializers.CharField(allow_null=True, allow_blank=True)
    address3 = serializers.CharField(allow_null=True, allow_blank=True)
    city = serializers.CharField(allow_null=True, allow_blank=True)
    company = serializers.CharField(allow_null=True, allow_blank=True)
    country = serializers.CharField(allow_null=True, allow_blank=True)
    email = serializers.CharField(allow_null=True, allow_blank=True)
    firstName = serializers.CharField(allow_null=True, allow_blank=True)
    middleName = serializers.CharField(allow_null=True, allow_blank=True)
    lastName = serializers.CharField(allow_null=True, allow_blank=True)
    licenseNumber = serializers.CharField(allow_null=True, allow_blank=True)
    postalCode = serializers.CharField(allow_null=True, allow_blank=True)
    phone = serializers.CharField(allow_null=True, allow_blank=True)
    passportNumber = serializers.CharField(allow_null=True, allow_blank=True)
    response = serializers.CharField(allow_null=True, allow_blank=True, default=None)
    ssn = serializers.CharField(allow_null=True, allow_blank=True, default=None)
    state = serializers.CharField(allow_null=True, allow_blank=True)
    title = serializers.CharField(allow_null=True, allow_blank=True)
    username = serializers.CharField(allow_blank=True, allow_null=True)


class SecurityNoteVaultSerializer(serializers.Serializer):
    type = serializers.IntegerField(required=False)
    response = serializers.CharField(allow_null=True, allow_blank=True, default=None)


class VaultItemSerializer(serializers.Serializer):
    collectionIds = serializers.ListField(
        child=serializers.CharField(max_length=128), required=False, allow_null=True, allow_empty=True
    )
    organizationId = serializers.CharField(required=False, allow_null=True, default=None)
    folderId = serializers.CharField(required=False, allow_null=True, default=None, allow_blank=True)
    favorite = serializers.BooleanField(default=False)
    fields = ItemFieldSerializer(many=True, required=False, allow_null=True)
    score = serializers.FloatField(default=0, min_value=0)
    reprompt = serializers.ChoiceField(choices=[0, 1], default=0, allow_null=True)
    view_password = serializers.BooleanField(default=True)
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
        detail = {
            "edit": True,
            "view_password": validated_data.get("view_password", True),
            "type": validated_data.get("type"),
            "user_id": self.context["request"].user.user_id,
            "created_by_id": self.context["request"].user.user_id,
            "organization_id": validated_data.get("organizationId"),
            "team_id": validated_data.get("organizationId"),
            "folder_id": validated_data.get("folderId"),
            "favorite": validated_data.get("favorite", False),
            "reprompt": validated_data.get("reprompt", 0),
            "attachments": None,
            "fields": validated_data.get("fields"),
            "score": validated_data.get("score", 0),
            "collection_ids": validated_data.get("collectionIds"),
        }
        # Cipher data
        detail.update({"data": get_cipher_detail_data(validated_data)})
        return detail

    def to_internal_value(self, data):
        data["favorite"] = data.get("favorite", False) or False
        return super(VaultItemSerializer, self).to_internal_value(data)


class UpdateVaultItemSerializer(VaultItemSerializer):
    pass


class MultipleItemIdsSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.CharField(), allow_empty=False, allow_null=False, required=True)

    def validate(self, data):
        ids = data.get("ids")
        if not ids:
            raise serializers.ValidationError(detail={"ids": ["This field is required"]})
        if len(ids) > 10000:
            raise serializers.ValidationError({"non_field_errors": [gen_error("5001")]})
        return data


class DetailCipherSerializer(SyncCipherSerializer):
    def to_representation(self, instance):
        return super(DetailCipherSerializer, self).to_representation(instance)


class UpdateCipherUseSerializer(serializers.Serializer):
    favorite = serializers.BooleanField(default=False, required=False)
    use = serializers.BooleanField(default=False, required=False)


class MultipleMoveSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.CharField(), allow_empty=False, allow_null=False, required=True)
    folderId = serializers.CharField(allow_null=True)

    def validate(self, data):
        ids = data.get("ids")
        if not ids:
            raise serializers.ValidationError(detail={"ids": ["This field is required"]})
        if len(ids) > 200:
            raise serializers.ValidationError(detail={"ids": ["You can only select up to 200 items at a time"]})
        return data


class SyncOfflineVaultItemSerializer(VaultItemSerializer):
    id = serializers.CharField(required=False, allow_null=True)
    deletedDate = serializers.FloatField(required=False, allow_null=True)

    def to_representation(self, instance):
        data = super(SyncOfflineVaultItemSerializer, self).to_representation(instance)
        data["deleted_date"] = self.validated_data.get("deletedDate")
        return data


class SyncOfflineFolderSerializer(FolderSerializer):
    id = serializers.CharField(required=False, allow_null=True)


class FolderRelationshipSerializer(serializers.Serializer):
    key = serializers.IntegerField(min_value=0)
    value = serializers.IntegerField(min_value=0)


class SyncOfflineCipherSerializer(serializers.Serializer):
    ciphers = SyncOfflineVaultItemSerializer(many=True)
    folders = SyncOfflineFolderSerializer(many=True)
    folderRelationships = FolderRelationshipSerializer(many=True)

    def validate(self, data):
        ciphers = data.get("ciphers", [])
        folders = data.get("folders", [])
        folder_relationships = data.get("folderRelationships", [])
        if len(ciphers) > 1000:
            raise serializers.ValidationError(detail={"ciphers": ["You cannot import this much data at once"]})
        if len(folder_relationships) > 1000:
            raise serializers.ValidationError(
                detail={"folderRelationships": ["You cannot import this much data at once"]})
        if len(folders) > 200:
            raise serializers.ValidationError(detail={"folders": ["You cannot import this much data at once"]})
        return data
