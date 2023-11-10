from locker_server.shared.constants.missions import REWARD_TYPE_PREMIUM
from locker_server.shared.external_services.user_reward_mission.mission import Mission


class ReferralMission(Mission):
    def __init__(self, mission_type: str, extra_requirements=None):
        super().__init__(mission_type=mission_type, extra_requirements=extra_requirements)
        self.reward_type = REWARD_TYPE_PREMIUM
        self.reward_value = 30 * 86400      # 1 month

    def check_mission_completion(self, input_data):
        pass
