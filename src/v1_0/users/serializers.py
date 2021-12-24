from rest_framework import serializers

from shared.constants.ciphers import KDF_TYPE
from shared.constants.transactions import PLAN_TYPE_PM_PRO, PLAN_TYPE_PM_BUSINESS, PLAN_TYPE_PM_AGENCY
from shared.constants.device_type import LIST_CLIENT_ID, LIST_DEVICE_TYPE
from cystack_models.models.members.team_members import TeamMember


class EncryptedPairKey(serializers.Serializer):
    encrypted_private_key = serializers.CharField()
    public_key = serializers.CharField()


class UserPwdSerializer(serializers.Serializer):
    kdf = serializers.IntegerField(default=0)
    kdf_iterations = serializers.IntegerField(default=100000)
    key = serializers.CharField()
    keys = EncryptedPairKey(many=False)
    master_password_hash = serializers.CharField(allow_blank=False)
    master_password_hint = serializers.CharField(allow_blank=True)
    score = serializers.FloatField(required=False, allow_null=True)
    trial_plan = serializers.ChoiceField(
        required=False, default=PLAN_TYPE_PM_PRO, choices=[PLAN_TYPE_PM_PRO, PLAN_TYPE_PM_BUSINESS, PLAN_TYPE_PM_AGENCY]
    )

    def validate(self, data):
        kdf_type = data.get("kdf_type", 0)
        if not KDF_TYPE.get(kdf_type):
            raise serializers.ValidationError(detail={"kdf": ["This KDF Type is not valid"]})
        kdf_iterations = data.get("kdf_iterations", 100000)
        if kdf_iterations < 5000 or kdf_iterations > 1000000:
            raise serializers.ValidationError(detail={
                "kdf_iterations": ["KDF iterations must be between 5000 and 1000000"]
            })
        return data


class UserSessionSerializer(serializers.Serializer):
    client_id = serializers.ChoiceField(choices=LIST_CLIENT_ID)
    device_identifier = serializers.CharField()
    device_name = serializers.CharField(required=False, allow_blank=True)
    device_type = serializers.IntegerField(required=False)
    password = serializers.CharField()

    def validate(self, data):
        device_type = data.get("device_type")
        if device_type and device_type not in LIST_DEVICE_TYPE:
            raise serializers.ValidationError(detail={"device_type": ["The device type is not valid"]})
        return data


class UserPwdInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ('id', 'access_time', 'role')
        read_only_fields = ('id', 'access_time', 'role')

    def to_representation(self, instance):
        data = super(UserPwdInvitationSerializer, self).to_representation(instance)
        data["status"] = instance.status
        data["team"] = {
            "id": instance.team.id,
            "organization_id": instance.team.id,
            "name": instance.team.name
        }
        return data


class UserMasterPasswordHashSerializer(serializers.Serializer):
    master_password_hash = serializers.CharField()

    def validate(self, data):
        user = self.context["request"].user
        master_password_hash = data.get("master_password_hash")
        if user.check_master_password(master_password_hash) is False:
            raise serializers.ValidationError(detail={"master_password_hash": ["The master password is not correct"]})
        return data


class UserChangePasswordSerializer(serializers.Serializer):
    key = serializers.CharField()
    master_password_hash = serializers.CharField()
    new_master_password_hash = serializers.CharField()

    def validate(self, data):
        user = self.context["request"].user
        master_password_hash = data.get("master_password_hash")
        if user.check_master_password(master_password_hash) is False:
            raise serializers.ValidationError(detail={"master_password_hash": ["The master password is not correct"]})
        return data
