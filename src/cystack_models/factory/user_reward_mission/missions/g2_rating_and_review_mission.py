from typing import Dict

from cystack_models.factory.user_reward_mission.mission import Mission
from shared.constants.missions import REWARD_TYPE_PROMO_CODE


class G2RatingAndReviewMission(Mission):
    def __init__(self, mission_type: str, extra_requirements=None):
        super().__init__(mission_type=mission_type, extra_requirements=extra_requirements)
        self.reward_type = REWARD_TYPE_PROMO_CODE
        self.reward_value = 5

    def check_mission_completion(self, input_data: Dict):
        return False
