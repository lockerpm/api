from rest_framework import serializers

from cystack_models.models.payments.promo_codes import PromoCode
from cystack_models.models.user_rewards.user_reward_missions import UserRewardMission
from v1_0.resources.serializers import RewardMissionSerializer


class UserRewardMissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRewardMission
        fields = ('status', 'is_claimed', 'completed_time')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        mission_serializer = RewardMissionSerializer(instance.mission, many=False)
        data["mission"] = mission_serializer.data
        return data


class UserRewardCheckCompletedSerializer(serializers.Serializer):
    user_identifier = serializers.CharField(max_length=255, allow_null=True)


class UserExtensionInstallCheckCompletedSerializer(serializers.Serializer):
    user_identifier = serializers.CharField(max_length=255)
    browser = serializers.CharField(max_length=128)


class ListRewardPromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = ('id', 'created_time', 'expired_time', 'valid', 'code', 'value')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["description"] = {
            "vi": instance.description_vi,
            "en": instance.description_en
        }
        data["type"] = instance.type_id
        return data
