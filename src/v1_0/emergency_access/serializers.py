from rest_framework import serializers

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
        return data


class InviteEmergencyAccessSerializer(serializers.Serializer):
    grantee_id = serializers.IntegerField(allow_null=True, required=False, default=None)
    email = serializers.EmailField(allow_null=True, required=False, default=None)
    type = serializers.ChoiceField(choices=[EMERGENCY_ACCESS_TYPE_VIEW, EMERGENCY_ACCESS_TYPE_TAKEOVER])
    wait_time_days = serializers.IntegerField(min_value=1, max_value=90)

    def validate(self, data):
        grantee_id = data.get("grantee_id")
        email = data.get("email")
        if not grantee_id and not email:
            raise serializers.ValidationError(detail={'email': ["Either email or grantee_id is required"]})
        if grantee_id:
            try:
                grantee = User.objects.get(user_id=grantee_id)
                data["grantee"] = grantee
            except User.DoesNotExist:
                raise serializers.ValidationError(detail={'email': ["Grantee email does not exist"]})
        return data


class PasswordEmergencyAccessSerializer(serializers.Serializer):
    key = serializers.CharField()
    new_master_password_hash = serializers.CharField()

