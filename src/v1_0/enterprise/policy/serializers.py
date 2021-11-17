from rest_framework import serializers

from cystack_models.models.policy.policy import Policy


class PolicyDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = ('min_password_length', 'max_password_length', 'password_composition',
                  'failed_login_attempts', 'failed_login_duration', 'failed_login_block_time')

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
        # failed_login_attempts = data.get("failed_login_attempts")
        # if failed_login_attempts and failed_login_attempts < 0:
        #     raise serializers.ValidationError(detail={"failed_login_attempts": ["This field is not valid"]})
        # failed_login_duration = data.get("failed_login_duration")
        # if failed_login_duration and failed_login_duration < 0:
        #     raise serializers.ValidationError(detail={"failed_login_duration": ["This field is not valid"]})
        # failed_login_block_time = data.get("failed_login_block_time")
        # if failed_login_block_time and failed_login_block_time < 0:
        #     raise serializers.ValidationError(detail={"failed_login_block_time": ["This field is not valid"]})

        return data

    def update(self, instance, validated_data):
        min_password_length = validated_data.get("min_password_length")
        max_password_length = validated_data.get("max_password_length")
        password_composition = validated_data.get("password_composition", instance.password_composition)
        failed_login_attempts = validated_data.get("failed_login_attempts")
        failed_login_duration = validated_data.get("failed_login_duration", instance.failed_login_duration)
        failed_login_block_time = validated_data.get("failed_login_block_time", instance.failed_login_block_time)

        instance.min_password_length = min_password_length
        instance.max_password_length = max_password_length
        instance.password_composition = password_composition
        instance.failed_login_attempts = failed_login_attempts
        instance.failed_login_duration = failed_login_duration
        instance.failed_login_block_time = failed_login_block_time
        instance.save()
        return instance

    def to_representation(self, instance):
        data = super(PolicyDetailSerializer, self).to_representation(instance)
        data["team"] = {
            "id": instance.team_id,
            "name": instance.team.name,
        }
        return data

