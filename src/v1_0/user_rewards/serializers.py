from rest_framework import serializers

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
