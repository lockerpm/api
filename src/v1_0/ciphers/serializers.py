from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from core.settings import CORE_CONFIG
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
        if vault_type == 1:
            if not login:
                raise serializers.ValidationError(detail={"login": ["This field is required"]})
            if login.get("totp") and not data.get("organizationId"):
                raise serializers.ValidationError(detail={
                    "organizationId": ["This field is required when using time OTP"]
                })
        if vault_type == 2 and not secure_note:
            raise serializers.ValidationError(detail={"secureNote": ["This field is required"]})
        if vault_type == 3 and not card:
            raise serializers.ValidationError(detail={"card": ["This field is required"]})
        if vault_type == 4 and not identity:
            raise serializers.ValidationError(detail={"identity": ["This field is required"]})

        # Check team id, folder ids
        organization_id = data.get("organizationId")
        collection_ids = data.get("collectionIds", [])
        if organization_id:
            try:
                team_member = user.team_members.get(
                    team_id=organization_id, role_id__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN],
                )
                # Get team object and check team is locked?
                team_obj = team_member.team
                if not team_repository.is_activated(team=team_obj):
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

        return data
