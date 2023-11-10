import json

from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.constants.missions import USER_MISSION_STATUS_NOT_STARTED


class AbstractUserRewardMissionORM(models.Model):
    user = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="user_reward_missions"
    )
    mission = models.ForeignKey(
        locker_server_settings.LS_MISSION_MODEL, on_delete=models.CASCADE, related_name="user_reward_missions"
    )
    status = models.CharField(max_length=64, default=USER_MISSION_STATUS_NOT_STARTED)
    is_claimed = models.BooleanField(default=False)
    completed_time = models.IntegerField(null=True)
    answer = models.CharField(max_length=512, blank=True, null=True, default=None)

    class Meta:
        abstract = True
        unique_together = ('user', 'mission')

    @classmethod
    def create_multiple_user_reward_missions(cls, user_id: int, mission_ids, **data):
        raise NotImplementedError

    def get_answer(self):
        if not self.answer:
            return {}
        try:
            return json.loads(str(self.answer))
        except json.JSONDecodeError:
            return self.answer
