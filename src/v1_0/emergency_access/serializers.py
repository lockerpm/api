from rest_framework import serializers

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
