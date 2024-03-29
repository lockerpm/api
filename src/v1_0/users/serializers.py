from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from core.settings import CORE_CONFIG
from shared.constants.account import LOGIN_METHOD_PASSWORD, LOGIN_METHOD_PASSWORDLESS
from shared.constants.ciphers import KDF_TYPE
from shared.constants.transactions import *
from shared.constants.device_type import LIST_CLIENT_ID, LIST_DEVICE_TYPE
from cystack_models.models.members.team_members import TeamMember
from cystack_models.models.user_plans.pm_plans import PMPlan
from cystack_models.models.users.devices import Device


class EncryptedPairKey(serializers.Serializer):
    encrypted_private_key = serializers.CharField()
    public_key = serializers.CharField()


class UserPwdSerializer(serializers.Serializer):
    kdf = serializers.IntegerField(default=0)
    kdf_iterations = serializers.IntegerField(default=100000)
    key = serializers.CharField()
    keys = EncryptedPairKey(many=False)
    master_password_hash = serializers.CharField(allow_blank=False)
    master_password_hint = serializers.CharField(allow_blank=True, max_length=128)
    score = serializers.FloatField(required=False, allow_null=True)
    trial_plan = serializers.ChoiceField(
        choices=[PLAN_TYPE_PM_FREE, PLAN_TYPE_PM_PREMIUM, PLAN_TYPE_PM_FAMILY, PLAN_TYPE_PM_ENTERPRISE],
        required=False, allow_null=True
    )
    is_trial_promotion = serializers.BooleanField(default=False, allow_null=True, required=False)
    enterprise_name = serializers.CharField(required=False, allow_null=True)
    # team_key = serializers.CharField(required=False, allow_null=True)
    # collection_name = serializers.CharField(required=False, allow_null=True)

    def validate(self, data):
        kdf_type = data.get("kdf_type", 0)
        if not KDF_TYPE.get(kdf_type):
            raise serializers.ValidationError(detail={"kdf": ["This KDF Type is not valid"]})
        kdf_iterations = data.get("kdf_iterations", 100000)
        if kdf_iterations < 5000 or kdf_iterations > 1000000:
            raise serializers.ValidationError(detail={
                "kdf_iterations": ["KDF iterations must be between 5000 and 1000000"]
            })

        trial_plan = data.get("trial_plan")
        if trial_plan:
            try:
                trial_plan_obj = PMPlan.objects.get(alias=trial_plan)
                data["trial_plan_obj"] = trial_plan_obj
            except PMPlan.DoesNotExist:
                raise serializers.ValidationError(detail={"trial_plan": ["The trial plan does not exist"]})

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
    new_master_password_hint = serializers.CharField(allow_blank=True, max_length=128, required=False)
    score = serializers.FloatField(required=False, allow_null=True)
    login_method = serializers.ChoiceField(choices=[LOGIN_METHOD_PASSWORD, LOGIN_METHOD_PASSWORDLESS], required=False)

    def validate(self, data):
        user = self.context["request"].user
        master_password_hash = data.get("master_password_hash")
        if user.check_master_password(master_password_hash) is False:
            raise serializers.ValidationError(detail={"master_password_hash": ["The master password is not correct"]})

        # Check login method: if user sets normal login method, we will check enterprise policy
        login_method = data.get("login_method")     # or user.login_method
        if login_method and login_method == LOGIN_METHOD_PASSWORD and user.enterprise_require_passwordless is True:
            raise serializers.ValidationError(detail={"login_method": ["Your enterprise requires passwordless method"]})
        return data


class UserNewPasswordSerializer(serializers.Serializer):
    key = serializers.CharField()
    new_master_password_hash = serializers.CharField()
    new_master_password_hint = serializers.CharField(allow_blank=True, max_length=128, required=False)
    score = serializers.FloatField(required=False, allow_null=True)
    login_method = serializers.ChoiceField(choices=[LOGIN_METHOD_PASSWORD, LOGIN_METHOD_PASSWORDLESS])

    def validate(self, data):
        user = self.context["request"].user
        login_method = data.get("login_method")  # or user.login_method
        if login_method and login_method == LOGIN_METHOD_PASSWORD and user.enterprise_require_passwordless is True:
            raise serializers.ValidationError(detail={"login_method": ["Your enterprise requires passwordless method"]})
        return data


class UserCheckPasswordSerializer(serializers.Serializer):
    master_password_hash = serializers.CharField()


class DeviceFcmSerializer(serializers.Serializer):
    fcm_id = serializers.CharField(max_length=255, allow_null=True)
    device_identifier = serializers.CharField(max_length=128)

    def validate(self, data):
        user = self.context["request"].user
        device_identifier = data.get("device_identifier")
        try:
            device = user.user_devices.get(device_identifier=device_identifier)
            data["device"] = device
        except ObjectDoesNotExist:
            raise serializers.ValidationError(detail={"device_identifier": [
                "This device does not exist"
            ]})
        return data


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ('client_id', 'device_name', 'device_type', 'device_identifier', 'last_login')

    def to_representation(self, instance):
        data = super(UserDeviceSerializer, self).to_representation(instance)
        data["os"] = instance.get_os()
        data["browser"] = instance.get_browser()
        data["is_active"] = instance.device_access_tokens.filter().exists()
        return data


class ListUserSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {
            "id": instance.user_id,
            "internal_id": instance.internal_id,
            "creation_data": instance.creation_date,
            "revision_data": instance.revision_date,
            "first_login": instance.first_login,
            "activated": instance.activated,
            "activated_data": instance.activated_date,
            "account_revision_date": instance.account_revision_date,
            "master_password_score": instance.master_password_score,
            "timeout": instance.timeout,
            "timeout_action": instance.timeout_action
        }
        action = self.context["view"].action
        if action == "list_users":
            user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
            data["current_plan"] = user_repository.get_current_plan(
                user=instance, scope=settings.SCOPE_PWD_MANAGER
            ).get_plan_type_alias()
        return data


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
