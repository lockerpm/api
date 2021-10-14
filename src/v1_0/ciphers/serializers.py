import json

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from core.settings import CORE_CONFIG
from shared.constants.ciphers import *
from shared.constants.members import *
from shared.error_responses.error import gen_error


class ItemFieldSerializer(serializers.Serializer):
    name = serializers.CharField()
    response = serializers.CharField(required=False, allow_null=True, default=None)
    type = serializers.IntegerField()
    value = serializers.CharField()


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
    type = serializers.IntegerField()
    response = serializers.CharField(allow_null=True, allow_blank=True, default=None)


class VaultItemSerializer(serializers.Serializer):
    collectionIds = serializers.ListField(
        child=serializers.CharField(max_length=128), required=False, allow_null=True, allow_empty=True
    )
    organizationId = serializers.CharField(required=False, allow_null=True, default=None)
    folderId = serializers.CharField(required=False, allow_null=True, default=None)
    favorite = serializers.BooleanField(default=False)
    fields = ItemFieldSerializer(many=True, required=False, allow_null=True)
    score = serializers.FloatField(default=0, min_value=0)
    reprompt = serializers.ChoiceField(choices=[0, 1], default=0, allow_null=True)
    name = serializers.CharField()
    notes = serializers.CharField(allow_blank=True, allow_null=True)
    type = serializers.IntegerField()
    login = LoginVaultSerializer(required=False, many=False, allow_null=True)
    secureNote = SecurityNoteVaultSerializer(required=False, many=False, allow_null=True)
    card = CardVaultSerializer(required=False, many=False, allow_null=True)
    identity = IdentityVaultSerializer(required=False, many=False, allow_null=True)

    def validate(self, data):
        user = self.context["request"].user
        team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()

        vault_type = data.get("type")
        if vault_type < 1 or vault_type > 4:
            raise serializers.ValidationError(detail={"type": ["The type does not exist"]})
        login = data.get("login", {})
        secure_note = data.get("secureNote")
        card = data.get("card")
        identity = data.get("identity")
        if vault_type == CIPHER_TYPE_LOGIN:
            if not login:
                raise serializers.ValidationError(detail={"login": ["This field is required"]})
            if login.get("totp") and not data.get("organizationId"):
                raise serializers.ValidationError(detail={
                    "organizationId": ["This field is required when using time OTP"]
                })
        if vault_type == CIPHER_TYPE_NOTE and not secure_note:
            raise serializers.ValidationError(detail={"secureNote": ["This field is required"]})
        if vault_type == CIPHER_TYPE_CARD and not card:
            raise serializers.ValidationError(detail={"card": ["This field is required"]})
        if vault_type == CIPHER_TYPE_IDENTITY and not identity:
            raise serializers.ValidationError(detail={"identity": ["This field is required"]})

        # Check folder id
        folder_id = data.get("folderId")
        if folder_id and user.folders.filter(id=folder_id).exists() is False:
            raise serializers.ValidationError(detail={"folderId": ["This folder does not exist"]})

        # Check team id, collection ids
        organization_id = data.get("organizationId")
        collection_ids = data.get("collectionIds", [])
        if organization_id:
            try:
                team_member = user.team_members.get(
                    team_id=organization_id, role_id__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN],
                )
                # Get team object and check team is locked?
                team_obj = team_member.team
                if not team_obj.key:
                    raise serializers.ValidationError(detail={"organizationId": [
                        "This team does not exist", "Team này không tồn tại"
                    ]})
                if team_repository.is_locked(team=team_obj):
                    raise serializers.ValidationError({"non_field_errors": [gen_error("3003")]})
                data["team"] = team_obj

                if not collection_ids:
                    default_collection_id = team_repository.get_default_collection(team=team_obj).id
                    data["collectionIds"] = [default_collection_id]
                else:
                    team_collections_ids = team_repository.get_list_collection_ids(team=team_obj)
                    for collection_id in collection_ids:
                        if collection_id not in list(team_collections_ids):
                            raise serializers.ValidationError(detail={
                                "collectionIds": ["The team collection id {} does not exist".format(collection_id)]
                            })
                        # Check member folder
                        # CHANGE LATER ...

                    data["collectionIds"] = list(set(collection_ids))

            except ObjectDoesNotExist:
                raise serializers.ValidationError(detail={"organizationId": [
                    "This team does not exist", "Team này không tồn tại"
                ]})
        else:
            data["organizationId"] = None
            data["collectionIds"] = []
            data["team"] = None

        return data

    def save(self, **kwargs):
        validated_data = self.validated_data
        cipher_type = validated_data.get("type")
        detail = {
            "edit": True,
            "view_password": True,
            "type": cipher_type,
            "user_id": self.context["request"].user.user_id,
            "organization_id": validated_data.get("organizationId"),
            "team_id": validated_data.get("organizationId"),
            "folder_id": validated_data.get("folderId"),
            "favorite": validated_data.get("favorite", False),
            "reprompt": validated_data.get("reprompt", 0),
            "attachments": None,
            "fields": validated_data.get("fields"),
            "score": validated_data.get("score", 0),
            "collection_ids": validated_data.get("collectionIds")
        }
        # Login data
        if cipher_type == CIPHER_TYPE_LOGIN:
            detail["data"] = dict(validated_data.get("login"))
        elif cipher_type == CIPHER_TYPE_CARD:
            detail["data"] = dict(validated_data.get("card"))
        elif cipher_type == CIPHER_TYPE_IDENTITY:
            detail["data"] = dict(validated_data.get("identity"))
        elif cipher_type == CIPHER_TYPE_NOTE:
            detail["data"] = dict(validated_data.get("secureNote"))
        detail["data"]["name"] = validated_data.get("name")
        if validated_data.get("notes"):
            detail["data"]["notes"] = validated_data.get("notes")
        print(detail)
        return detail


class UpdateVaultItemSerializer(VaultItemSerializer):
    def save(self, **kwargs):
        cipher = kwargs.get("cipher")
        validated_data = self.validated_data
        if cipher.team_id is None and validated_data.get("organizationId"):
            raise serializers.ValidationError(detail={"organizationId": [
                "You can not change team of cipher when update. Please share this cipher to change team"
            ]})
        return super(UpdateVaultItemSerializer, self).save(**kwargs)


class MutipleItemIdsSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.CharField(), allow_empty=False, allow_null=False, required=True)

    def validate(self, data):
        ids = data.get("ids")
        if not ids:
            raise serializers.ValidationError(detail={"ids": ["This field is required"]})
        if len(ids) > 200:
            raise serializers.ValidationError(detail={"ids": ["You can only select up to 200 items at a time"]})
        return data


class MultipleMoveSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.CharField(), allow_empty=False, allow_null=False, required=True)
    folderId = serializers.CharField(allow_null=True)

    def validate(self, data):
        user = self.context["request"].user
        ids = data.get("ids")
        if not ids:
            raise serializers.ValidationError(detail={"ids": ["This field is required"]})
        if len(ids) > 200:
            raise serializers.ValidationError(detail={"ids": ["You can only select up to 200 items at a time"]})

        folder_id = data.get("folderId")
        if folder_id and user.folders.filter(id=folder_id).exists() is False:
            raise serializers.ValidationError(detail={"folderId": ["This folder does not exist"]})
        return data
