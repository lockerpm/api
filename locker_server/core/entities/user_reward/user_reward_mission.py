import json

from locker_server.core.entities.user.user import User
from locker_server.core.entities.user_reward.mission import Mission
from locker_server.shared.constants.missions import USER_MISSION_STATUS_NOT_STARTED


class UserRewardMission(object):
    def __init__(self, user_reward_mission_id: int, user: User, mission=Mission,
                 status: str = USER_MISSION_STATUS_NOT_STARTED, is_claimed: bool = False, completed_time: int = None,
                 answer: str = None):
        self._user_reward_mission_id = user_reward_mission_id
        self._user = user
        self._mission = mission
        self._status = status
        self._is_claimed = is_claimed
        self._completed_time = completed_time
        self._answer = answer

    @property
    def user_reward_mission_id(self):
        return self._user_reward_mission_id

    @property
    def user(self):
        return self._user

    @property
    def mission(self):
        return self._mission

    @property
    def status(self):
        return self._status

    @property
    def is_claimed(self):
        return self._is_claimed

    @property
    def completed_time(self):
        return self._completed_time

    @property
    def answer(self):
        return self._answer

    def get_answer(self):
        if not self.answer:
            if self.mission.mission_id == "extension_installation_and_review":
                return []
            return {}
        try:
            return json.loads(str(self.answer))
        except json.JSONDecodeError:
            return self.answer
