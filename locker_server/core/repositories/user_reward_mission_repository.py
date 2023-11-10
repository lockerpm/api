from abc import ABC, abstractmethod
from typing import List, Optional, NoReturn

from locker_server.core.entities.user_reward.user_reward_mission import UserRewardMission


class UserRewardMissionRepository(ABC):

    # ------------------------ List UserRewardMission resource ------------------- #
    @abstractmethod
    def list_user_reward_missions(self, user_id: int, **filters) -> List[UserRewardMission]:
        pass

    # ------------------------ Get UserRewardMission resource --------------------- #
    @abstractmethod
    def get_user_reward_mission_by_id(self, user_reward_mission_id: str) -> Optional[UserRewardMission]:
        pass

    @abstractmethod
    def get_user_reward_by_mission_id(self, user_id: int, mission_id: str, available: bool = True) \
            -> Optional[UserRewardMission]:
        pass

    @abstractmethod
    def get_user_available_promo_code_value(self, user_id: int) -> int:
        pass

    # ------------------------ Create UserRewardMission resource --------------------- #
    @abstractmethod
    def create_user_reward_mission(self, user_reward_mission_create_data) -> Optional[UserRewardMission]:
        pass

    @abstractmethod
    def create_multiple_user_reward_missions(self, user_id: int, mission_ids, **data) -> NoReturn:
        pass

    # ------------------------ Update UserRewardMission resource --------------------- #

    @abstractmethod
    def update_user_reward_mission(self, user_reward_mission_id: str, user_reward_mission_update_data) \
            -> Optional[UserRewardMission]:
        pass

    # ------------------------ Delete UserRewardMission resource --------------------- #
