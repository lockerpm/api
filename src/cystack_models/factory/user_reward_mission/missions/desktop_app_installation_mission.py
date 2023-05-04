from typing import Dict

from cystack_models.factory.user_reward_mission.mission import Mission
from shared.constants.device_type import CLIENT_ID_DESKTOP


class DesktopAppInstallationMission(Mission):

    def check_mission_completion(self, input_data: Dict):
        user = input_data.get("user")
        if not user:
            return False
        return user.user_devices.filter(client_id=CLIENT_ID_DESKTOP).exists()
