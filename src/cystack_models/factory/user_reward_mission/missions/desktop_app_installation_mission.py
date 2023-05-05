from typing import Dict

from cystack_models.factory.user_reward_mission.mission import Mission
from shared.constants.device_type import CLIENT_ID_DESKTOP
from shared.constants.missions import REWARD_TYPE_PROMO_CODE


class DesktopAppInstallationMission(Mission):
    def __init__(self, mission_type: str, extra_requirements=None):
        super().__init__(mission_type=mission_type, extra_requirements=extra_requirements)
        self.reward_type = REWARD_TYPE_PROMO_CODE
        self.reward_value = 5

    def check_mission_completion(self, input_data: Dict):
        user = input_data.get("user")
        if not user:
            return False
        return user.user_devices.filter(client_id=CLIENT_ID_DESKTOP).exists()
