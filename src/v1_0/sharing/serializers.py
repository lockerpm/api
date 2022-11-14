from rest_framework import serializers

from core.settings import CORE_CONFIG
from shared.constants.ciphers import *
from shared.constants.members import *
from cystack_models.models.members.team_members import TeamMember
from cystack_models.models.enterprises.groups.groups import EnterpriseGroup
from shared.utils.app import get_cipher_detail_data
from v1_0.ciphers.serializers import ItemFieldSerializer, LoginVaultSerializer, SecurityNoteVaultSerializer, \
    CardVaultSerializer, IdentityVaultSerializer, CryptoAccountSerializer, CryptoWalletSerializer


class UserPublicKeySerializer(serializers.Serializer):
    user_id = serializers.IntegerField()


class MemberShareSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(allow_null=True, required=False)
    email = serializers.EmailField(allow_null=True, required=False)
    hide_passwords = serializers.BooleanField(default=False)
    role = serializers.ChoiceField(choices=[MEMBER_ROLE_ADMIN, MEMBER_ROLE_MEMBER])
    key = serializers.CharField(allow_null=True, required=False)

    def validate(self, data):
        user_id = data.get("user_id")
        email = data.get("email")
        if not user_id and not email:
            raise serializers.ValidationError(detail={
                "user_id": ["The user id or email is required"],
                "email": ["The email or user id is required"]
            })
        return data


class GroupMemberShareSeralizer(serializers.Serializer):
    user_id = serializers.IntegerField(allow_null=True, required=False)
    email = serializers.EmailField(allow_null=True, required=False)
    key = serializers.CharField(allow_null=True, required=False)

    def validate(self, data):
        user_id = data.get("user_id")
        email = data.get("email")
        if not user_id and not email:
            raise serializers.ValidationError(detail={
                "user_id": ["The user id or email is required"],
                "email": ["The email or user id is required"]
            })
        return data


class GroupShareSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=128)
    role = serializers.ChoiceField(choices=[MEMBER_ROLE_ADMIN, MEMBER_ROLE_MEMBER])
    members = GroupMemberShareSeralizer(many=True)

    def validate(self, data):
        group_id = data.get("group_id")
        try:
            enterprise_group = EnterpriseGroup.objects.get(id=group_id)
        except EnterpriseGroup.DoesNotExist:
            raise serializers.ValidationError(detail={"id": ["The group id does not exist"]})
        group_members = enterprise_group.groups_members.values('member__user_id', 'member__email')
        members_user_ids = [member.get("member__user_id") for member in group_members if member.get("member__user_id")]
        members_emails = [member.get("member__email") for member in group_members if member.get("member__email")]
        members = data.get("members")
        user_ids = [member.get("user_id") for member in members if member.get("user_id")]
        emails = [member.get("email") for member in members if member.get("email")]
        if any(user_id not in members_user_ids for user_id in user_ids):
            raise serializers.ValidationError(detail={"members": ["The member user id are not valid"]})
        if any(email not in members_emails for email in emails):
            raise serializers.ValidationError(detail={"members": ["The member emails are not valid"]})

        return data


class CipherShareSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=128)
    score = serializers.FloatField(default=0, min_value=0)
    reprompt = serializers.ChoiceField(choices=[0, 1], default=0, allow_null=True)
    # Detail Ciphers
    name = serializers.CharField()
    notes = serializers.CharField(allow_blank=True, allow_null=True)
    type = serializers.ChoiceField(choices=list(set(LIST_CIPHER_TYPE) - set(IMMUTABLE_CIPHER_TYPES)))
    # view_password = serializers.BooleanField(default=True)
    fields = ItemFieldSerializer(many=True, required=False, allow_null=True)
    login = LoginVaultSerializer(required=False, many=False, allow_null=True)
    secureNote = SecurityNoteVaultSerializer(required=False, many=False, allow_null=True)
    card = CardVaultSerializer(required=False, many=False, allow_null=True)
    identity = IdentityVaultSerializer(required=False, many=False, allow_null=True)
    cryptoAccount = CryptoAccountSerializer(required=False, many=False, allow_null=True)
    cryptoWallet = CryptoWalletSerializer(required=False, many=False, allow_null=True)


class FolderShareSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=128)
    name = serializers.CharField()
    ciphers = CipherShareSerializer(many=True, required=False)


class SharingSerializer(serializers.Serializer):
    sharing_key = serializers.CharField(required=False, allow_null=True)
    members = MemberShareSerializer(many=True)
    groups = GroupShareSerializer(many=True, required=False, allow_null=True)
    cipher = CipherShareSerializer(many=False, required=False, allow_null=True)
    folder = FolderShareSerializer(many=False, required=False, allow_null=True)

    def validate(self, data):
        cipher = data.get("cipher")
        folder = data.get("folder")
        groups = data.get("groups")
        if not cipher and not folder:
            raise serializers.ValidationError(detail={
                "cipher": ["The cipher or folder is required"],
                "folder": ["The folder or cipher is required"]
            })
        if cipher and folder:
            raise serializers.ValidationError(detail={
                "cipher": ["You can only share a cipher or a folder"],
                "folder": ["You can only share a cipher or a folder"]
            })
        if groups:
            user = self.context["request"].user
            user_enterprise_group_ids = EnterpriseGroup.get_list_user_group_ids(user=user)
            if any(group.get("id") not in user_enterprise_group_ids for group in groups):
                raise serializers.ValidationError(detail={"groups": ["The groups are not valid"]})
        return data

    @staticmethod
    def __get_shared_cipher_data(cipher):
        shared_cipher_data = {
            "id": cipher.get("id"),
            "type": cipher.get("type"),
            "score": cipher.get("score", 0),
            "reprompt": cipher.get("reprompt", 0),
            "attachments": None,
            "fields": cipher.get("fields"),
            "collection_ids": [],
            "data": get_cipher_detail_data(cipher)
        }
        return shared_cipher_data

    def save(self, **kwargs):
        validated_data = self.validated_data
        cipher = validated_data.get("cipher")

        # Get shared cipher data if the user shares a cipher
        if cipher:
            validated_data["shared_cipher_data"] = self.__get_shared_cipher_data(cipher=cipher)

        # Get shared cipher data of the folder if the user shares a folder
        folder = validated_data.get("folder")
        if folder:
            shared_ciphers = []
            ciphers = folder.get("ciphers") or []
            for cipher in ciphers:
                shared_ciphers.append(self.__get_shared_cipher_data(cipher=cipher))
            folder["ciphers"] = shared_ciphers

        return validated_data


class CipherMemberSharingSerializer(serializers.Serializer):
    members = MemberShareSerializer(many=True)
    groups = GroupShareSerializer(many=True, required=False, allow_null=True)
    cipher = CipherShareSerializer(many=False, required=True, allow_null=False)


class FolderMemberSharingSerializer(serializers.Serializer):
    members = MemberShareSerializer(many=True)
    groups = GroupShareSerializer(many=True, required=False, allow_null=True)
    folder = FolderShareSerializer(many=False, required=True, allow_null=False)


class MultipleSharingSerializer(serializers.Serializer):
    sharing_key = serializers.CharField(required=False, allow_null=True)
    ciphers = CipherMemberSharingSerializer(many=True, required=False, allow_null=True)
    folders = FolderMemberSharingSerializer(many=True, required=False, allow_null=True)

    def validate(self, data):
        ciphers = data.get("ciphers")
        folders = data.get("folders")
        if not ciphers and not folders:
            raise serializers.ValidationError(detail={
                "ciphers": ["The ciphers or folders are required"],
                "folder": ["The folders or ciphers is required"]
            })
        if ciphers and folders:
            raise serializers.ValidationError(detail={
                "ciphers": ["You can only share the ciphers or the folders"],
                "folders": ["You can only share the ciphers or the folders"]
            })

        # Limit the number of the ciphers
        if ciphers and len(ciphers) >= 20:
            raise serializers.ValidationError(detail={
                "ciphers": ["The maximum number of ciphers is 20"]
            })
        if folders and len(folders) >= 5:
            raise serializers.ValidationError(detail={
                "folders": ["The maximum number of folders is 5"]
            })

        # Validate groups
        if ciphers:
            for cipher in ciphers:
                self.__check_groups(groups=cipher.get("groups"))
        if folders:
            for folder in folders:
                self.__check_groups(groups=folder.get("groups"))

        return data

    @staticmethod
    def __get_shared_cipher_data(cipher):
        shared_cipher_data = {
            "type": cipher.get("type"),
            "score": cipher.get("score", 0),
            "reprompt": cipher.get("reprompt", 0),
            "attachments": None,
            "fields": cipher.get("fields"),
            "collection_ids": [],
            "data": get_cipher_detail_data(cipher)
        }
        return shared_cipher_data

    def __check_groups(self, groups):
        user = self.context["request"].user
        user_enterprise_group_ids = EnterpriseGroup.get_list_user_group_ids(user=user)
        if any(group.get("id") not in user_enterprise_group_ids for group in groups):
            raise serializers.ValidationError(detail={"groups": ["The groups are not valid"]})
        return groups

    def save(self, **kwargs):
        validated_data = self.validated_data
        ciphers = validated_data.get("ciphers")

        # Get shared ciphers data if the user shares the ciphers
        if ciphers:
            for cipher in ciphers:
                cipher["shared_cipher_data"] = self.__get_shared_cipher_data(cipher=cipher.get("cipher"))

        # Get shared cipher data of the folders if the user shares the folders
        folders = validated_data.get("folders")
        if folders:
            for folder in folders:
                shared_ciphers = []
                ciphers = folder.get("ciphers") or []
                for cipher in ciphers:
                    shared_ciphers.append(self.__get_shared_cipher_data(cipher=cipher))
                folder["ciphers"] = shared_ciphers

        return validated_data


class StopSharingSerializer(serializers.Serializer):
    cipher = CipherShareSerializer(many=False, required=False, allow_null=True)
    folder = FolderShareSerializer(many=False, required=False, allow_null=True)

    def validate(self, data):
        cipher = data.get("cipher")
        folder = data.get("folder")
        if not cipher and not folder:
            raise serializers.ValidationError(detail={
                "cipher": ["The cipher or folder is required"],
                "folder": ["The folder or cipher is required"]
            })
        if cipher and folder:
            raise serializers.ValidationError(detail={
                "cipher": ["You can only stop sharing a cipher or a folder"],
                "folder": ["You can only stop sharing a cipher or a folder"]
            })
        return data

    def __get_personal_cipher_data(self, cipher):
        shared_cipher_data = {
            "id": cipher.get("id"),
            "type": cipher.get("type"),
            "score": cipher.get("score", 0),
            "reprompt": cipher.get("reprompt", 0),
            "fields": cipher.get("fields"),
            "data": get_cipher_detail_data(cipher)
        }
        return shared_cipher_data

    def save(self, **kwargs):
        validated_data = self.validated_data
        cipher = validated_data.get("cipher")

        # Get personal cipher data if the user stop sharing a cipher
        if cipher:
            validated_data["personal_cipher_data"] = self.__get_personal_cipher_data(cipher=cipher)

        # Get personal cipher data of the collection if the user stop sharing a collection
        folder = validated_data.get("folder")
        if folder:
            personal_ciphers = []
            ciphers = folder.get("ciphers") or []
            for cipher in ciphers:
                personal_ciphers.append(self.__get_personal_cipher_data(cipher=cipher))
            folder["ciphers"] = personal_ciphers

        return validated_data


class SharingInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ('id', 'access_time', 'role')
        read_only_fields = ('id', 'access_time', 'role')

    def to_representation(self, instance):
        team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()
        sharing_repository = CORE_CONFIG["repositories"]["ISharingRepository"]()
        data = super(SharingInvitationSerializer, self).to_representation(instance)
        team = instance.team
        owner = team_repository.get_primary_member(team=team)
        item_type = "folder" if team.collections.all().exists() else "cipher"
        if item_type == "cipher":
            share_cipher = team.ciphers.first()
            cipher_type = share_cipher.type if share_cipher else None
        else:
            cipher_type = None
        data["status"] = instance.status
        data["team"] = {
            "id": instance.team.id,
            "organization_id": instance.team.id,
            "name": instance.team.name
        }
        data["owner"] = owner.user_id
        data["item_type"] = item_type
        data["share_type"] = sharing_repository.get_personal_share_type(member=instance)
        data["cipher_type"] = cipher_type
        data["hide_passwords"] = instance.hide_passwords
        return data


class AddMemberSerializer(serializers.Serializer):
    members = MemberShareSerializer(many=True)


class UpdateInvitationRoleSerializer(serializers.Serializer):
    hide_passwords = serializers.BooleanField(default=False)
    role = serializers.ChoiceField(choices=[MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER])


class UpdateShareFolderSerializer(serializers.Serializer):
    name = serializers.CharField()


class StopSharingFolderSerializer(serializers.Serializer):
    folder = FolderShareSerializer(many=False, required=True)

    def __get_personal_cipher_data(self, cipher):
        shared_cipher_data = {
            "id": cipher.get("id"),
            "type": cipher.get("type"),
            "score": cipher.get("score", 0),
            "reprompt": cipher.get("reprompt", 0),
            "fields": cipher.get("fields"),
            "data": get_cipher_detail_data(cipher)
        }
        return shared_cipher_data

    def save(self, **kwargs):
        validated_data = self.validated_data

        # Get personal cipher data of the collection if the user stop sharing a collection
        folder = validated_data.get("folder")
        personal_ciphers = []
        ciphers = folder.get("ciphers") or []
        for cipher in ciphers:
            personal_ciphers.append(self.__get_personal_cipher_data(cipher=cipher))
        folder["ciphers"] = personal_ciphers

        return validated_data


class AddItemShareFolderSerializer(serializers.Serializer):
    cipher = CipherShareSerializer(many=False, required=True)

    def __get_share_cipher_data(self, cipher):
        shared_cipher_data = {
            "id": cipher.get("id"),
            "type": cipher.get("type"),
            "score": cipher.get("score", 0),
            "reprompt": cipher.get("reprompt", 0),
            "fields": cipher.get("fields"),
            "data": get_cipher_detail_data(cipher)
        }
        return shared_cipher_data

    def save(self, **kwargs):
        validated_data = self.validated_data
        validated_data["cipher"] = self.__get_share_cipher_data(cipher=validated_data.get("cipher"))
        return validated_data
