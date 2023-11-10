from typing import Dict

from locker_server.containers.containers import device_service
from locker_server.shared.constants.device_type import CLIENT_ID_DESKTOP
from locker_server.shared.constants.missions import REWARD_TYPE_PROMO_CODE
from locker_server.shared.external_services.user_reward_mission.mission import Mission


class DesktopAppInstallationMission(Mission):
    def __init__(self, mission_type: str, extra_requirements=None):
        super().__init__(mission_type=mission_type, extra_requirements=extra_requirements)
        self.reward_type = REWARD_TYPE_PROMO_CODE
        self.reward_value = 5

    def check_mission_completion(self, input_data: Dict):
        user = input_data.get("user")
        if not user:
            return False
        desktop_devices = device_service.list_devices(**{
            "user_id": user.user_id,
            "client_id": CLIENT_ID_DESKTOP
        })
        return True if desktop_devices else False
