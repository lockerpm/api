from rest_framework import serializers

from locker_server.shared.constants.account import LOGIN_METHOD_PASSWORD, LOGIN_METHOD_PASSWORDLESS
from locker_server.shared.constants.ciphers import KDF_TYPE
from locker_server.shared.constants.device_type import LIST_CLIENT_ID, LIST_DEVICE_TYPE
from locker_server.shared.constants.factor2 import LIST_FA2_METHOD
from locker_server.shared.constants.lang import LANG_ENGLISH, LANG_VIETNAM
from locker_server.shared.constants.transactions import *


class UserMeSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "email": instance.email,
            "name": instance.full_name,
            "timeout": instance.timeout,
            "timeout_action": instance.timeout_action,
            "is_pwd_manager": instance.activated,
            "pwd_user_id": str(instance.user_id),
            "language": instance.language,
            "is_passwordless": self.context.get("is_passwordless_func")(instance.user_id),
            "avatar": instance.get_avatar()

        }
        show_key_param = self.context["request"].query_params.get("show_key", "0")
        if show_key_param == "1":
            data.update({
                "key": instance.key,
                "public_key": instance.public_key,
                "private_key": instance.private_key
            })
        return data


class UserScoreUpdateSerializer(serializers.Serializer):
    cipher0 = serializers.IntegerField(min_value=0, required=False)
    cipher1 = serializers.IntegerField(min_value=0, required=False)
    cipher2 = serializers.IntegerField(min_value=0, required=False)
    cipher3 = serializers.IntegerField(min_value=0, required=False)
    cipher4 = serializers.IntegerField(min_value=0, required=False)
    cipher5 = serializers.IntegerField(min_value=0, required=False)
    cipher6 = serializers.IntegerField(min_value=0, required=False)
    cipher7 = serializers.IntegerField(min_value=0, required=False)


class UserUpdateMeSerializer(serializers.Serializer):
    timeout = serializers.IntegerField(allow_null=True, min_value=-1, required=False)
    timeout_action = serializers.ChoiceField(choices=["lock", "logOut"], required=False)
    scores = UserScoreUpdateSerializer(allow_null=True, required=False, many=False)
    language = serializers.ChoiceField(choices=[LANG_ENGLISH, LANG_VIETNAM], required=False)
    name = serializers.CharField(required=False, max_length=512, allow_blank=False)

    def to_internal_value(self, data):
        name = data.get("name")
        if name:
            data.update({
                "full_name": name
            })
        return data


class EncryptedPairKey(serializers.Serializer):
    encrypted_private_key = serializers.CharField()
    public_key = serializers.CharField()


class UserRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    full_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    kdf = serializers.IntegerField(default=0)
    kdf_iterations = serializers.IntegerField(default=100000)
    key = serializers.CharField()
    keys = EncryptedPairKey(many=False)
    master_password_hash = serializers.CharField(allow_blank=False)
    master_password_hint = serializers.CharField(allow_blank=True, max_length=128)
    score = serializers.FloatField(required=False, allow_null=True, default=0)
    trial_plan = serializers.ChoiceField(
        choices=[PLAN_TYPE_PM_FREE, PLAN_TYPE_PM_PREMIUM, PLAN_TYPE_PM_FAMILY, PLAN_TYPE_PM_ENTERPRISE],
        required=False, allow_null=True
    )
    is_trial_promotion = serializers.BooleanField(default=False, allow_null=True, required=False)
    enterprise_name = serializers.CharField(required=False, allow_null=True)

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
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField()
    client_id = serializers.ChoiceField(choices=LIST_CLIENT_ID)
    device_identifier = serializers.CharField()
    device_name = serializers.CharField(required=False, allow_blank=True)
    device_type = serializers.IntegerField(required=False)

    def validate(self, data):
        device_type = data.get("device_type")
        if device_type and device_type not in LIST_DEVICE_TYPE:
            raise serializers.ValidationError(detail={"device_type": ["The device type is not valid"]})
        return data


class UserSessionByOtpSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField()
    client_id = serializers.ChoiceField(choices=LIST_CLIENT_ID)
    device_identifier = serializers.CharField()
    device_name = serializers.CharField(required=False, allow_blank=True)
    device_type = serializers.IntegerField(required=False)
    otp = serializers.CharField(required=True)
    method = serializers.ChoiceField(choices=LIST_FA2_METHOD)

    def validate(self, data):
        device_type = data.get("device_type")
        if device_type and device_type not in LIST_DEVICE_TYPE:
            raise serializers.ValidationError(detail={"device_type": ["The device type is not valid"]})
        return data


class DeviceFcmSerializer(serializers.Serializer):
    fcm_id = serializers.CharField(max_length=255, allow_null=True)
    device_identifier = serializers.CharField(max_length=128)


class UserChangePasswordSerializer(serializers.Serializer):
    key = serializers.CharField()
    master_password_hash = serializers.CharField()
    new_master_password_hash = serializers.CharField()
    new_master_password_hint = serializers.CharField(allow_blank=True, max_length=128, required=False)
    score = serializers.FloatField(required=False, allow_null=True)
    login_method = serializers.ChoiceField(choices=[LOGIN_METHOD_PASSWORD, LOGIN_METHOD_PASSWORDLESS], required=False)


class UserNewPasswordSerializer(serializers.Serializer):
    key = serializers.CharField()
    new_master_password_hash = serializers.CharField()
    new_master_password_hint = serializers.CharField(allow_blank=True, max_length=128, required=False)
    score = serializers.FloatField(required=False, allow_null=True)
    login_method = serializers.ChoiceField(choices=[LOGIN_METHOD_PASSWORD, LOGIN_METHOD_PASSWORDLESS])


class UserCheckPasswordSerializer(serializers.Serializer):
    master_password_hash = serializers.CharField()
    email = serializers.EmailField()


class UserMasterPasswordHashSerializer(serializers.Serializer):
    master_password_hash = serializers.CharField()


class UpdateOnboardingProcessSerializer(serializers.Serializer):
    vault_to_dashboard = serializers.BooleanField(required=False)
    welcome = serializers.BooleanField(required=False)
    tutorial = serializers.BooleanField(required=False)
    tutorial_process = serializers.ListField(
        child=serializers.CharField(max_length=128), required=False, allow_empty=True, max_length=16
    )
    enterprise_onboarding = serializers.ListField(
        child=serializers.IntegerField(), required=False, max_length=10
    )
    enterprise_onboarding_skip = serializers.BooleanField(required=False)

    def validate(self, data):
        enterprise_onboarding = data.get("enterprise_onboarding")
        if enterprise_onboarding:
            if len([e for e in enterprise_onboarding if e > 10]) > 0:
                raise serializers.ValidationError(detail={
                    "enterprise_onboarding": ["The enterprise onboarding is not valid"]
                })
        return data


class UserPwdInvitationSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.team_member_id,
            "access_time": instance.access_time,
            "role": instance.role.name,
            "status": instance.status,
            "team": {
                "id": instance.team.team_id,
                "organization_id": instance.team.team_id,
                "name": instance.team.name
            }
        }
        return data


class UserDeviceSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "client_id": instance.client_id,
            "device_name": instance.device_name,
            "device_type": instance.device_type,
            "device_identifier": instance.device_identifier,
            "last_login": instance.last_login,
            "os": instance.os,
            "browser": instance.browser,
            "is_active": instance.is_active
        }
        return data


class PreloginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class UserResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(max_length=256)
    new_key = serializers.CharField(required=False)
