from abc import ABC, abstractmethod
from typing import List, Optional

from locker_server.core.entities.user_reward.mission import Mission


class MissionRepository(ABC):

    # ------------------------ List Mission resource ------------------- #
    @abstractmethod
    def list_available_mission_ids(self) -> List[str]:
        pass

    # ------------------------ Get Mission resource --------------------- #

    # ------------------------ Create Mission resource --------------------- #

    # ------------------------ Update Mission resource --------------------- #

    # ------------------------ Delete Mission resource --------------------- #
