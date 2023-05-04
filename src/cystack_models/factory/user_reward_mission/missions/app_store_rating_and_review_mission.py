from typing import Dict

from cystack_models.factory.user_reward_mission.mission import Mission


class AppStoreRatingAndReviewMission(Mission):

    def check_mission_completion(self, input_data: Dict):
        user = input_data.get("user")
        url = ""

        return False
