from rest_framework import serializers

from core.settings import CORE_CONFIG
from shared.constants.ciphers import *
from shared.constants.members import *
from cystack_models.models.members.team_members import TeamMember
from v1_0.ciphers.serializers import ItemFieldSerializer, LoginVaultSerializer, SecurityNoteVaultSerializer, \
    CardVaultSerializer, IdentityVaultSerializer


class UserPublicKeySerializer(serializers.Serializer):
    user_id = serializers.IntegerField()


class MemberShareSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(allow_null=True, required=False)
    email = serializers.EmailField(allow_null=True, required=False)
    hide_passwords = serializers.BooleanField(default=False)
    role = serializers.ChoiceField(choices=[MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER])
    key = serializers.CharField(allow_null=True, required=False)

    def validate(self, data):
        user_id = data.get("user_id")
        email = data.get("email")
        key = data.get("key")
        if not user_id and not email:
            raise serializers.ValidationError(detail={
                "user_id": ["The user id or email is required"],
                "email": ["The email or user id is required"]
            })
        if user_id and not key:
            raise serializers.ValidationError(detail={"key": ["This field is required"]})
        return data


class CipherShareSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=128)
    score = serializers.FloatField(default=0, min_value=0)
    reprompt = serializers.ChoiceField(choices=[0, 1], default=0, allow_null=True)
    # Detail Ciphers
    name = serializers.CharField()
    notes = serializers.CharField(allow_blank=True, allow_null=True)
    type = serializers.ChoiceField(choices=LIST_CIPHER_TYPE)
    # view_password = serializers.BooleanField(default=True)
    fields = ItemFieldSerializer(many=True, required=False, allow_null=True)
    login = LoginVaultSerializer(required=False, many=False, allow_null=True)
    secureNote = SecurityNoteVaultSerializer(required=False, many=False, allow_null=True)
    card = CardVaultSerializer(required=False, many=False, allow_null=True)
    identity = IdentityVaultSerializer(required=False, many=False, allow_null=True)


class FolderShareSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=128)
    name = serializers.CharField()
    ciphers = CipherShareSerializer(many=True, required=False)


class SharingSerializer(serializers.Serializer):
    sharing_key = serializers.CharField(required=False, allow_null=True)
    members = MemberShareSerializer(many=True)
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
                "cipher": ["You can only share a cipher or a folder"],
                "folder": ["You can only share a cipher or a folder"]
            })
        return data

    def __get_shared_cipher_data(self, cipher):
        cipher_type = cipher.get("type")
        shared_cipher_data = {
            "type": cipher_type,
            "score": cipher.get("score", 0),
            "reprompt": cipher.get("reprompt", 0),
            "attachments": None,
            "fields": cipher.get("fields"),
            "collection_ids": [],
        }
        # Login data
        if cipher_type == CIPHER_TYPE_LOGIN:
            shared_cipher_data["data"] = dict(cipher.get("login"))
        elif cipher_type == CIPHER_TYPE_CARD:
            shared_cipher_data["data"] = dict(cipher.get("card"))
        elif cipher_type == CIPHER_TYPE_IDENTITY:
            shared_cipher_data["data"] = dict(cipher.get("identity"))
        elif cipher_type == CIPHER_TYPE_NOTE:
            shared_cipher_data["data"] = dict(cipher.get("secureNote"))
        elif cipher_type == CIPHER_TYPE_TOTP:
            shared_cipher_data["data"] = dict(cipher.get("secureNote"))
        shared_cipher_data["data"]["name"] = cipher.get("name")
        if cipher.get("notes"):
            shared_cipher_data["data"]["notes"] = cipher.get("notes")
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
            ciphers = validated_data.get("ciphers") or []
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
        cipher_type = cipher.get("type")
        shared_cipher_data = {
            "type": cipher_type,
            "score": cipher.get("score", 0),
            "reprompt": cipher.get("reprompt", 0),
            "fields": cipher.get("fields")
        }
        # Login data
        if cipher_type == CIPHER_TYPE_LOGIN:
            shared_cipher_data["data"] = dict(cipher.get("login"))
        elif cipher_type == CIPHER_TYPE_CARD:
            shared_cipher_data["data"] = dict(cipher.get("card"))
        elif cipher_type == CIPHER_TYPE_IDENTITY:
            shared_cipher_data["data"] = dict(cipher.get("identity"))
        elif cipher_type == CIPHER_TYPE_NOTE:
            shared_cipher_data["data"] = dict(cipher.get("secureNote"))
        elif cipher_type == CIPHER_TYPE_TOTP:
            shared_cipher_data["data"] = dict(cipher.get("secureNote"))
        shared_cipher_data["data"]["name"] = cipher.get("name")
        if cipher.get("notes"):
            shared_cipher_data["data"]["notes"] = cipher.get("notes")
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
            ciphers = validated_data.get("ciphers") or []
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
        return data


class UpdateInvitationRoleSerializer(serializers.Serializer):
    hide_passwords = serializers.BooleanField(default=False)
    role = serializers.ChoiceField(choices=[MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER])
