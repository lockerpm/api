import json

from django.db import models

from cystack_models.models.user_rewards.missions import Mission
from cystack_models.models.users.users import User
from shared.constants.missions import USER_MISSION_STATUS_NOT_STARTED


class UserRewardMission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_reward_missions")
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="user_reward_missions")
    status = models.CharField(max_length=64, default=USER_MISSION_STATUS_NOT_STARTED)
    is_claimed = models.BooleanField(default=False)
    completed_time = models.IntegerField(null=True)
    answer = models.CharField(max_length=512, blank=True, null=True, default=None)

    class Meta:
        db_table = 'cs_user_reward_missions'
        unique_together = ('user', 'mission')

    @classmethod
    def create_multiple_user_reward_missions(cls, user, mission_ids, **data):
        user_reward_mission_objs = []
        for mission_id in mission_ids:
            user_reward_mission_objs.append(cls(
                user=user,
                mission_id=mission_id,
                status=data.get("status", USER_MISSION_STATUS_NOT_STARTED),
                is_claimed=data.get("is_claimed", False),
                completed_time=data.get("completed")
            ))
        cls.objects.bulk_create(user_reward_mission_objs, ignore_conflicts=True, batch_size=50)

    def get_answer(self):
        if not self.answer:
            return {}
        try:
            return json.loads(str(self.answer))
        except json.JSONDecodeError:
            return self.answer
