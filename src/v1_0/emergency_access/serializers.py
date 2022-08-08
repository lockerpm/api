from rest_framework import serializers

from core.settings import CORE_CONFIG
from shared.constants.emergency_access import *
from cystack_models.models.users.users import User
from cystack_models.models.emergency_access.emergency_access import EmergencyAccess


class EmergencyAccessGranteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyAccess
        fields = ('id', 'creation_date', 'revision_date', 'last_notification_date', 'recovery_initiated_date',
                  'status', 'type', 'wait_time_days', 'key_encrypted')
        read_only_fields = ('id', 'creation_date', 'revision_date', 'last_notification_date', 'recovery_initiated_date')

    def to_representation(self, instance):
        data = super(EmergencyAccessGranteeSerializer, self).to_representation(instance)
        data["object"] = "emergencyAccessGranteeDetails"
        data["email"] = instance.email
        data["grantee_user_id"] = instance.grantee_id
        data["grantee_pwd_user_id"] = instance.grantee.internal_id if instance.grantee else None
        return data


class EmergencyAccessGrantorSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyAccess
        fields = ('id', 'creation_date', 'revision_date', 'last_notification_date', 'recovery_initiated_date',
                  'status', 'type', 'wait_time_days', 'key_encrypted')
        read_only_fields = ('id', 'creation_date', 'revision_date', 'last_notification_date', 'recovery_initiated_date')

    def to_representation(self, instance):
        data = super(EmergencyAccessGrantorSerializer, self).to_representation(instance)
        data["object"] = "emergencyAccessGrantorDetails"
        data["grantor_user_id"] = instance.grantor_id
        data["grantor_pwd_user_id"] = instance.grantor.internal_id if instance.grantor else None
        return data


class InviteEmergencyAccessSerializer(serializers.Serializer):
    grantee_id = serializers.IntegerField(allow_null=True, required=False, default=None)
    email = serializers.EmailField(allow_null=True, required=False, default=None)
    type = serializers.ChoiceField(choices=[EMERGENCY_ACCESS_TYPE_VIEW, EMERGENCY_ACCESS_TYPE_TAKEOVER])
    wait_time_days = serializers.IntegerField(min_value=1, max_value=90)
    key = serializers.CharField(max_length=512, allow_null=True, required=False)

    def validate(self, data):
        emergency_repository = CORE_CONFIG["repositories"]["IEmergencyAccessRepository"]()
        user = self.context["request"].user
        emergency_type = data.get("type")
        grantee_id = data.get("grantee_id")
        email = data.get("email")
        if not grantee_id and not email:
            raise serializers.ValidationError(detail={'email': ["Either email or grantee_id is required"]})
        if grantee_id:
            try:
                grantee = User.objects.get(user_id=grantee_id, activated=True)
                if emergency_repository.check_emergency_existed(
                    grantor=user, emergency_type=emergency_type, grantee=grantee
                ) is True:
                    raise serializers.ValidationError(detail={"email": ["The emergency already exists"]})
                data["grantee"] = grantee
            except User.DoesNotExist:
                raise serializers.ValidationError(detail={'email': ["Grantee email does not exist"]})
        else:
            if emergency_repository.check_emergency_existed(
                grantor=user, emergency_type=emergency_type, email=email
            ) is True:
                raise serializers.ValidationError(detail={"email": ["The emergency already exists"]})
        return data


class PasswordEmergencyAccessSerializer(serializers.Serializer):
    key = serializers.CharField()
    new_master_password_hash = serializers.CharField()

