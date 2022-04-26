from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from core.settings import CORE_CONFIG
from shared.constants.ciphers import *
from shared.constants.members import *
from shared.error_responses.error import gen_error
from shared.utils.app import diff_list, get_cipher_detail_data
from v1_0.folders.serializers import FolderSerializer
from v1_0.sync.serializers import SyncCipherSerializer


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
    folderId = serializers.CharField(required=False, allow_null=True, default=None)
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
        user = self.context["request"].user

        vault_type = data.get("type")
        login = data.get("login", {})
        secure_note = data.get("secureNote")
        card = data.get("card")
        identity = data.get("identity")
        crypto_account = data.get("cryptoAccount")
        crypto_wallet = data.get("cryptoWallet")
        if vault_type == CIPHER_TYPE_LOGIN and not login:
            raise serializers.ValidationError(detail={"login": ["This field is required"]})
        if vault_type == CIPHER_TYPE_NOTE and not secure_note:
            raise serializers.ValidationError(detail={"secureNote": ["This field is required"]})
        if vault_type == CIPHER_TYPE_CARD and not card:
            raise serializers.ValidationError(detail={"card": ["This field is required"]})
        if vault_type == CIPHER_TYPE_IDENTITY and not identity:
            raise serializers.ValidationError(detail={"identity": ["This field is required"]})
        # if vault_type == CIPHER_TYPE_TOTP and not secure_note:
        #     raise serializers.ValidationError(detail={"secureNote": ["This field is required"]})
        # if vault_type == CIPHER_TYPE_CRYPTO_ACCOUNT and not crypto_account:
        #     raise serializers.ValidationError(detail={"cryptoAccount": ["This field is required"]})
        # if vault_type == CIPHER_TYPE_CRYPTO_WALLET and not crypto_wallet:
        #     raise serializers.ValidationError(detail={"cryptoWallet": ["This field is required"]})

        # Check folder id
        folder_id = data.get("folderId")
        if folder_id and user.folders.filter(id=folder_id).exists() is False:
            raise serializers.ValidationError(detail={"folderId": ["This folder does not exist"]})

        # Check team id, collection ids
        data = self.validated_team(data)
        return data

    def validated_team(self, data):
        user = self.context["request"].user
        team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()
        organization_id = data.get("organizationId")
        collection_ids = data.get("collectionIds", [])
        if organization_id:
            try:
                team_member = user.team_members.get(
                    team_id=organization_id, role_id__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER],
                )
            except ObjectDoesNotExist:
                raise serializers.ValidationError(detail={"organizationId": [
                    "This team does not exist", "Team này không tồn tại"
                ]})
            # Get team object and check team is locked?
            team_obj = team_member.team
            if not team_obj.key:
                raise serializers.ValidationError(detail={"organizationId": [
                    "This team does not exist", "Team này không tồn tại"
                ]})
            if team_repository.is_locked(team=team_obj):
                raise serializers.ValidationError({"non_field_errors": [gen_error("3003")]})
            data["team"] = team_obj
            data["collectionIds"] = self.validate_collections(
                team_member=team_member, collection_ids=collection_ids
            )

        else:
            data["organizationId"] = None
            data["collectionIds"] = []
            data["team"] = None
        return data

    def validate_collections(self, team_member, collection_ids):
        team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()
        team_obj = team_member.team
        role_id = team_member.role_id
        if not collection_ids:
            try:
                default_collection = team_repository.get_default_collection(team=team_obj)
                default_collection_id = default_collection.id
            except ObjectDoesNotExist:
                raise serializers.ValidationError(detail={
                    "collectionIds": ["Not found any collections"]
                })
            if role_id == MEMBER_ROLE_MANAGER and \
                    team_member.collections_members.filter(collection_id=default_collection_id).exists() is False:
                raise serializers.ValidationError(detail={
                    "collectionIds": ["The team collection id {} does not exist".format(default_collection_id)]
                })
            return [default_collection_id]
        else:
            if role_id in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]:
                team_collections_ids = team_repository.get_list_collection_ids(team=team_obj)
            else:
                team_collections_ids = list(
                    team_member.collections_members.values_list('collection_id', flat=True)
                )
            for collection_id in collection_ids:
                if collection_id not in list(team_collections_ids):
                    raise serializers.ValidationError(detail={
                        "collectionIds": ["The team collection id {} does not exist".format(collection_id)]
                    })
            return list(set(collection_ids))

    def validated_plan(self, data):
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        cipher_repository = CORE_CONFIG["repositories"]["ICipherRepository"]()
        user = self.context["request"].user

        # Get limit cipher type from personal and team plans
        allow_cipher_type = user_repository.get_max_allow_cipher_type(user=user, personal_share=False)
        ciphers = cipher_repository.get_ciphers_created_by_user(user=user)

        vault_type = data.get("type")
        existed_ciphers_count = ciphers.filter(type=vault_type).count()
        # limit_vault_type = plan_obj.get_limit_ciphers_by_type(vault_type=vault_type)
        if vault_type == CIPHER_TYPE_LOGIN and allow_cipher_type.get(vault_type) and \
                existed_ciphers_count >= allow_cipher_type.get(vault_type):
            raise serializers.ValidationError(detail={"login": ["The maximum number of login ciphers is reached"]})
        if vault_type == CIPHER_TYPE_NOTE and allow_cipher_type.get(vault_type) and \
                existed_ciphers_count >= allow_cipher_type.get(vault_type):
            raise serializers.ValidationError(detail={"secureNote": ["The maximum number of note ciphers is reached"]})
        if vault_type == CIPHER_TYPE_CARD and allow_cipher_type.get(vault_type) and \
                existed_ciphers_count >= allow_cipher_type.get(vault_type):
            raise serializers.ValidationError(detail={"card": ["The maximum number of card ciphers is reached"]})
        if vault_type == CIPHER_TYPE_IDENTITY and allow_cipher_type.get(vault_type) and \
                existed_ciphers_count >= allow_cipher_type.get(vault_type):
            raise serializers.ValidationError(detail={"identity": ["The maximum number of identity ciphers is reached"]})
        if vault_type == CIPHER_TYPE_TOTP and allow_cipher_type.get(vault_type) and \
                existed_ciphers_count >= allow_cipher_type.get(vault_type):
            raise serializers.ValidationError(detail={"secureNote": ["The maximum number of totp ciphers is reached"]})
        if vault_type == CIPHER_TYPE_CRYPTO_ACCOUNT and allow_cipher_type.get(vault_type) and \
                existed_ciphers_count >= allow_cipher_type.get(vault_type):
            raise serializers.ValidationError(detail={"cryptoAccount": ["The maximum number of crypto ciphers is reached"]})
        if vault_type == CIPHER_TYPE_CRYPTO_WALLET and allow_cipher_type.get(vault_type) and \
                existed_ciphers_count >= allow_cipher_type.get(vault_type):
            raise serializers.ValidationError(detail={"cryptoWallet": ["The maximum number of crypto ciphers is reached"]})
        return data

    def save(self, **kwargs):
        validated_data = self.validated_data
        check_plan = kwargs.get("check_plan", False)
        if check_plan is True:
            validated_data = self.validated_plan(validated_data)

        cipher_type = validated_data.get("type")
        detail = {
            "edit": True,
            "view_password": validated_data.get("view_password", True),
            "type": cipher_type,
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
        detail["data"]["name"] = validated_data.get("name")
        if validated_data.get("notes"):
            detail["data"]["notes"] = validated_data.get("notes")

        return detail

    def to_internal_value(self, data):
        data["favorite"] = data.get("favorite", False) or False
        return super(VaultItemSerializer, self).to_internal_value(data)


class UpdateVaultItemSerializer(VaultItemSerializer):
    def validate_collections(self, team_member, collection_ids):
        team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()
        team_obj = team_member.team
        role_id = team_member.role_id
        if not collection_ids:
            # Get default collection
            try:
                default_collection = team_repository.get_default_collection(team=team_obj)
                default_collection_id = default_collection.id
                if role_id == MEMBER_ROLE_MANAGER and \
                        team_member.collections_members.filter(collection_id=default_collection_id).exists() is False:
                    raise serializers.ValidationError(detail={
                        "collectionIds": ["You do not have permission in default collections"]
                    })
                return [default_collection_id]
            except ObjectDoesNotExist:
                return []
        else:
            team_collection_ids = team_repository.get_list_collection_ids(team=team_obj)
            for collection_id in collection_ids:
                if collection_id not in list(team_collection_ids):
                    raise serializers.ValidationError(detail={
                        "collectionIds": ["The team collection id {} does not exist".format(collection_id)]
                    })
            return list(set(collection_ids))

    def save(self, **kwargs):
        cipher = kwargs.get("cipher")
        validated_data = self.validated_data
        if cipher.team_id is None and validated_data.get("organizationId"):
            raise serializers.ValidationError(detail={"organizationId": [
                "You can not change team of cipher when update. Please share this cipher to change team"
            ]})

        # Validate collection ids
        if cipher.team:
            team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()
            user = self.context["request"].user
            team_member = user.team_members.get(
                team_id=cipher.team_id, role_id__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER],
            )
            role_id = team_member.role_id
            cipher_collection_ids = list(cipher.collections_ciphers.values_list('collection_id', flat=True))
            collection_ids = validated_data.get("collectionIds", [])
            team_collection_ids = team_repository.get_list_collection_ids(team=cipher.team)
            if role_id in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]:
                member_collection_ids = team_collection_ids
            else:
                member_collection_ids = list(
                    team_member.collections_members.values_list('collection_id', flat=True)
                )
            remove_collection_ids = diff_list(cipher_collection_ids, collection_ids)
            add_collection_ids = diff_list(collection_ids, cipher_collection_ids)

            if remove_collection_ids:
                for member_collection_id in member_collection_ids:
                    if member_collection_id not in remove_collection_ids:
                        raise serializers.ValidationError(detail={"collectionIds": [
                            "You can not remove collection {}".format(member_collection_id)
                        ]})
            if add_collection_ids:
                for member_collection_id in member_collection_ids:
                    if member_collection_id not in add_collection_ids:
                        raise serializers.ValidationError(detail={"collectionIds": [
                            "You can not add collection {}".format(member_collection_id)
                        ]})

        return super(UpdateVaultItemSerializer, self).save(**kwargs)


class ShareVaultItemSerializer(VaultItemSerializer):
    def save(self, **kwargs):
        validated_data = self.validated_data
        if not validated_data.get("organizationId"):
            raise serializers.ValidationError(detail={"organizationId": [
                "This field is required", "Trường này là bắt buộc"
            ]})
        return super(ShareVaultItemSerializer, self).save(**kwargs)


class MutipleItemIdsSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.CharField(), allow_empty=False, allow_null=False, required=True)

    def validate(self, data):
        ids = data.get("ids")
        if not ids:
            raise serializers.ValidationError(detail={"ids": ["This field is required"]})
        if len(ids) > 10000:
            raise serializers.ValidationError({"non_field_errors": [gen_error("5001")]})
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


class FolderRelationshipSerializer(serializers.Serializer):
    key = serializers.IntegerField(min_value=0)
    value = serializers.IntegerField(min_value=0)


class ImportCipherSerializer(serializers.Serializer):
    ciphers = VaultItemSerializer(many=True)
    folders = FolderSerializer(many=True)
    folderRelationships = FolderRelationshipSerializer(many=True)

    def validate(self, data):
        folders = data.get("folders", [])
        folder_relationships = data.get("folderRelationships", [])
        ciphers = data.get("ciphers", [])
        if len(ciphers) > 2000:
            raise serializers.ValidationError(detail={"ciphers": ["You cannot import this much data at once"]})
        if len(folder_relationships) > 2000:
            raise serializers.ValidationError(detail={"folderRelationships": ["You cannot import this much data at once"]})
        if len(folders) > 400:
            raise serializers.ValidationError(detail={"folders": ["You cannot import this much data at once"]})

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


class DetailCipherSerializer(SyncCipherSerializer):
    def to_representation(self, instance):
        return super(DetailCipherSerializer, self).to_representation(instance)
