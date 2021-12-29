from rest_framework import serializers

from shared.constants.members import *
from cystack_models.models.members.team_members import TeamMember


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


class FolderShareSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=128)
    name = serializers.CharField()


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


class SharingInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ('id', 'access_time', 'role')
        read_only_fields = ('id', 'access_time', 'role')

    def to_representation(self, instance):
        data = super(SharingInvitationSerializer, self).to_representation(instance)
        data["status"] = instance.status
        data["team"] = {
            "id": instance.team.id,
            "organization_id": instance.team.id,
            "name": instance.team.name
        }
        return data
