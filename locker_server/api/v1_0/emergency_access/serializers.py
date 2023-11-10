from rest_framework import serializers

from locker_server.shared.constants.emergency_access import EMERGENCY_ACCESS_TYPE_VIEW, EMERGENCY_ACCESS_TYPE_TAKEOVER


class EmergencyAccessGranteeSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = {
            "object": "emergencyAccessGranteeDetails",
            "id": instance.emergency_access_id,
            "creation_date": instance.creation_date,
            "revision_date": instance.revision_date,
            "last_notification_date": instance.last_notification_date,
            "recovery_initiated_date": instance.recovery_initiated_date,
            "status": instance.status,
            "type": instance.emergency_access_type,
            "wait_time_days": instance.wait_time_days,
            "key_encrypted": instance.key_encrypted,
            "email": instance.email,
            "grantee_pwd_user_id": None,
        }
        if instance.grantee:
            data.update({
                "email": instance.grantee.email,
                "full_name": instance.grantee.full_name,
                "avatar": instance.grantee.get_avatar(),
                "grantee_pwd_user_id": instance.grantee.internal_id
            })
        return data


class EmergencyAccessGrantorSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "object": "emergencyAccessGrantorDetails",
            "id": instance.emergency_access_id,
            "creation_date": instance.creation_date,
            "revision_date": instance.revision_date,
            "last_notification_date": instance.last_notification_date,
            "recovery_initiated_date": instance.recovery_initiated_date,
            "status": instance.status,
            "type": instance.emergency_access_type,
            "wait_time_days": instance.wait_time_days,
            "key_encrypted": instance.key_encrypted,
            "grantor_pwd_user_id": instance.grantor.internal_id if instance.grantor else None
        }
        if instance.grantor:
            data.update({
                "email": instance.grantor.email,
                "full_name": instance.grantor.full_name,
                "avatar": instance.grantor.get_avatar()
            })
        return data


class InviteEmergencyAccessSerializer(serializers.Serializer):
    # grantee_id = serializers.IntegerField(allow_null=True, required=False, default=None)
    email = serializers.EmailField(allow_null=True, required=False, default=None)
    type = serializers.ChoiceField(choices=[EMERGENCY_ACCESS_TYPE_VIEW, EMERGENCY_ACCESS_TYPE_TAKEOVER])
    wait_time_days = serializers.IntegerField(min_value=1, max_value=90)
    key = serializers.CharField(max_length=512, allow_null=True, required=False)

    def validate(self, data):
        grantee_id = data.get("grantee_id")
        email = data.get("email")
        if not grantee_id and not email:
            raise serializers.ValidationError(detail={'email': ["Either email or grantee_id is required"]})
        return data


class PasswordEmergencyAccessSerializer(serializers.Serializer):
    key = serializers.CharField()
    new_master_password_hash = serializers.CharField()


class ViewOrgSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.team.team_id,
            "key": instance.key,
        }
        return data
