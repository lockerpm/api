from rest_framework import serializers

from cystack_models.models.enterprises.policy.policy import EnterprisePolicy


class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterprisePolicy
        fields = ('enabled', 'policy_type')
        read_only_fields = ('enabled', 'policy_type')

    def to_representation(self, instance):
        data = super(PolicySerializer, self).to_representation(instance)
        data["config"] = instance.get_config_json()
        return data


class UpdatePasswordPolicySerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    min_length = serializers.IntegerField(min_value=1, max_value=128, allow_null=True, required=False)
    require_lower_case = serializers.BooleanField(required=False)
    require_upper_case = serializers.BooleanField(required=False)
    require_special_character = serializers.BooleanField(required=False)
    require_digit = serializers.BooleanField(required=False)

    def save(self, **kwargs):
        config_obj = kwargs.get("config_obj")
        validated_data = self.validated_data
        enabled = validated_data.get("enabled")
        min_length = validated_data.get("min_length", config_obj.min_length)
        require_lower_case = validated_data.get("require_lower_case",  config_obj.require_lower_case)
        require_upper_case = validated_data.get("require_upper_case", config_obj.require_upper_case)
        require_special_character = validated_data.get(
            "require_special_character", config_obj.require_special_character
        )
        require_digit = validated_data.get("require_digit", config_obj.require_digit)

        config_obj.min_length = min_length
        config_obj.require_lower_case = require_lower_case
        config_obj.require_upper_case = require_upper_case
        config_obj.require_special_character = require_special_character
        config_obj.require_digit = require_digit
        config_obj.save()
        config_obj.policy.enabled = enabled
        config_obj.policy.save()
        return config_obj


class UpdateMasterPasswordPolicySerializer(UpdatePasswordPolicySerializer):
    """

    """


class UpdateFailedLoginPolicySerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    failed_login_attempts = serializers.IntegerField(allow_null=True, min_value=1, required=False)
    failed_login_duration = serializers.IntegerField(min_value=1, required=False)
    failed_login_block_time = serializers.IntegerField(min_value=1, required=False)
    failed_login_owner_email = serializers.BooleanField(required=False)

    def save(self, **kwargs):
        config_obj = kwargs.get("config_obj")
        validated_data = self.validated_data
        enabled = validated_data.get("enabled")
        failed_login_attempts = validated_data.get("failed_login_attempts", config_obj.failed_login_attempts)
        failed_login_duration = validated_data.get("failed_login_duration", config_obj.failed_login_duration)
        failed_login_block_time = validated_data.get("failed_login_block_time", config_obj.failed_login_block_time)
        failed_login_owner_email = validated_data.get("failed_login_owner_email", config_obj.failed_login_owner_email)

        config_obj.failed_login_attempts = failed_login_attempts
        config_obj.failed_login_duration = failed_login_duration
        config_obj.failed_login_block_time = failed_login_block_time
        config_obj.failed_login_owner_email = failed_login_owner_email
        config_obj.save()
        config_obj.policy.enabled = enabled
        config_obj.policy.save()
        return config_obj


class UpdatePasswordlessPolicySerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    only_allow_passwordless = serializers.BooleanField(required=False)

    def save(self, **kwargs):
        config_obj = kwargs.get("config_obj")
        validated_data = self.validated_data
        enabled = validated_data.get("enabled")
        only_allow_passwordless = validated_data.get("only_allow_passwordless", config_obj.only_allow_passwordless)

        config_obj.only_allow_passwordless = only_allow_passwordless
        config_obj.save()
        config_obj.policy.enabled = enabled
        config_obj.policy.save()
        return config_obj
