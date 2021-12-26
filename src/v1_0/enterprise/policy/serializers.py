from rest_framework import serializers

from cystack_models.models.policy.policy import Policy


class PolicyDetailSerializer(serializers.ModelSerializer):
    ip_allow = serializers.ListSerializer(child=serializers.CharField(max_length=16), allow_empty=True, required=False)
    ip_block = serializers.ListSerializer(child=serializers.CharField(max_length=16), allow_empty=True, required=False)

    class Meta:
        model = Policy
        fields = (
            'min_password_length', 'max_password_length',
            'password_composition', 'require_lower_case', 'require_upper_case', 'require_special_character',
            'require_digit', 'avoid_ambiguous_character',
            'ip_allow', 'ip_block',
            'block_mobile',
            'failed_login_attempts', 'failed_login_duration', 'failed_login_block_time', 'failed_login_owner_email'
        )

    def validate(self, data):
        min_password_length = data.get("min_password_length")
        if min_password_length and min_password_length < 1:
            raise serializers.ValidationError(detail={"min_password_length": ["The min password length is not valid"]})
        max_password_length = data.get("max_password_length")
        if max_password_length and max_password_length < 1:
            raise serializers.ValidationError(detail={"max_password_length": ["The max password length is not valid"]})
        if min_password_length and max_password_length and min_password_length > max_password_length:
            raise serializers.ValidationError(detail={
                "min_password_length": ["The min password and max password length are not valid"]
            })

        return data

    def update(self, instance, validated_data):
        min_password_length = validated_data.get("min_password_length")
        max_password_length = validated_data.get("max_password_length")
        password_composition = validated_data.get("password_composition", instance.password_composition)
        require_lower_case = validated_data.get("require_lower_case", instance.require_lower_case)
        require_upper_case = validated_data.get("require_upper_case", instance.require_upper_case)
        require_special_character = validated_data.get("require_special_character", instance.require_special_character)
        require_digit = validated_data.get("require_digit", instance.require_digit)
        avoid_ambiguous_character = validated_data.get("avoid_ambiguous_character", instance.avoid_ambiguous_character)
        ip_allow = validated_data.get("ip_allow", instance.get_list_ip_allow())
        ip_block = validated_data.get("ip_block", instance.get_list_ip_block())
        block_mobile = validated_data.get("block_mobile", instance.block_mobile)
        failed_login_attempts = validated_data.get("failed_login_attempts")
        failed_login_duration = validated_data.get("failed_login_duration", instance.failed_login_duration)
        failed_login_block_time = validated_data.get("failed_login_block_time", instance.failed_login_block_time)
        failed_login_owner_email = validated_data.get("failed_login_owner_email", instance.failed_login_owner_email)

        instance.min_password_length = min_password_length
        instance.max_password_length = max_password_length
        instance.password_composition = password_composition
        instance.require_lower_case = require_lower_case
        instance.require_upper_case = require_upper_case
        instance.require_special_character = require_special_character
        instance.require_digit = require_digit
        instance.avoid_ambiguous_character = avoid_ambiguous_character
        instance.ip_allow = ",".join(ip_allow)
        instance.ip_block = ",".join(ip_block)
        instance.block_mobile = block_mobile
        instance.failed_login_attempts = failed_login_attempts
        instance.failed_login_duration = failed_login_duration
        instance.failed_login_block_time = failed_login_block_time
        instance.failed_login_owner_email = failed_login_owner_email
        instance.save()
        return instance

    def to_representation(self, instance):
        data = super(PolicyDetailSerializer, self).to_representation(instance)
        data["ip_allow"] = instance.get_list_ip_allow()
        data["ip_block"] = instance.get_list_ip_block()
        data["team"] = {
            "id": instance.team_id,
            "name": instance.team.name,
        }
        return data

