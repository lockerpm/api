from typing import List, Optional, NoReturn, Tuple, Dict

from locker_server.core.entities.payment.promo_code import PromoCode
from locker_server.core.entities.user_reward.user_reward_mission import UserRewardMission
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.core.exceptions.user_reward_mission_exception import UserRewardMissionDoesNotExistException, \
    UserRewardPromoCodeInvalidException
from locker_server.core.repositories.mission_repository import MissionRepository
from locker_server.core.repositories.promo_code_repository import PromoCodeRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.core.repositories.user_reward_mission_repository import UserRewardMissionRepository
from locker_server.shared.constants.missions import REWARD_TYPE_PROMO_CODE, USER_MISSION_STATUS_REWARD_SENT
from locker_server.shared.constants.transactions import PROMO_PERCENTAGE, MISSION_REWARD_PROMO_PREFIX, DURATION_YEARLY
from locker_server.shared.utils.app import random_n_digit, now


class UserRewardMissionService:
    """
    This class represents Use Cases related user reward mission
    """

    def __init__(self, user_reward_mission_repository: UserRewardMissionRepository,
                 user_repository: UserRepository, mission_repository: MissionRepository,
                 promo_code_repository: PromoCodeRepository
                 ):
        self.user_reward_mission_repository = user_reward_mission_repository
        self.user_repository = user_repository
        self.mission_repository = mission_repository
        self.promo_code_repository = promo_code_repository

    def list_user_reward_mission(self, user_id: int, **filters) -> List[UserRewardMission]:
        return self.user_reward_mission_repository.list_user_reward_missions(
            user_id=user_id,
            **filters
        )

    def list_user_promo_codes(self, user_id: int) -> List[PromoCode]:
        return self.promo_code_repository.list_user_promo_codes(
            user_id=user_id
        )

    def get_user_reward_by_mission_id(self, user_id: int, mission_id: str, available: bool = True) \
            -> Optional[UserRewardMission]:
        user_reward_mission = self.user_reward_mission_repository.get_user_reward_by_mission_id(
            user_id=user_id,
            mission_id=mission_id,
            available=available
        )
        if not user_reward_mission:
            raise UserRewardMissionDoesNotExistException
        return user_reward_mission

    def gen_user_default_missions(self, user_id: int) -> NoReturn:
        user = self.user_repository.get_user_by_id(user_id=user_id)
        if not user:
            raise UserDoesNotExistException
        mission_ids = self.mission_repository.list_available_mission_ids()
        self.user_reward_mission_repository.create_multiple_user_reward_missions(
            user_id=user_id,
            mission_ids=mission_ids
        )

    def user_available_promo_code_value(self, user_id: int):
        return self.user_reward_mission_repository.get_user_available_promo_code_value(
            user_id=user_id
        )

    def user_used_promo_code_value(self, user_id: int):
        return self.promo_code_repository.get_used_promo_code_value(
            user_id=user_id
        )

    def claim_promo_code(self, user_id: int) -> PromoCode:
        self.gen_user_default_missions(user_id=user_id)
        max_available_promo_code_value = self.user_available_promo_code_value(user_id=user_id)
        used_promo_code_value = self.user_used_promo_code_value(user_id=user_id)
        available_promo_code_value = max(max_available_promo_code_value - used_promo_code_value, 0)
        if available_promo_code_value <= 0:
            raise UserRewardPromoCodeInvalidException
        code = f"{MISSION_REWARD_PROMO_PREFIX}{random_n_digit(n=8)}".upper()
        # This code is expired in a week
        expired_time = int(now() + 7 * 86400)
        promo_code_create_data = {
            "type": PROMO_PERCENTAGE,
            "expired_time": expired_time,
            "code": code,
            "value": available_promo_code_value,
            "duration": 1,
            "number_code": 1,
            "description_en": "Locker PromoCode Reward",
            "description_vi": "Locker PromoCode Reward",
            "only_user_id": user_id,
            "only_period": DURATION_YEARLY
        }
        new_promo_code = self.promo_code_repository.create_promo_code(
            promo_code_create_data=promo_code_create_data
        )
        self.promo_code_repository.delete_old_promo_code(
            user_id=user_id,
            exclude_promo_code_id=new_promo_code.promo_code_id
        )
        return new_promo_code

    def delete_promo_code_by_id(self, promo_code_id: str) -> NoReturn:
        self.promo_code_repository.delete_promo_code_by_id(
            promo_code_id=promo_code_id
        )

    def list_user_generated_promo_codes(self, user_id: int):
        generated_promo_codes = self.promo_code_repository.list_user_generated_promo_codes(user_id=user_id)
        return generated_promo_codes

    def get_claim(self, user_id: int) -> Dict:
        user_promo_code_reward_missions = self.list_user_reward_mission(user_id=user_id, **{
            "reward_type": REWARD_TYPE_PROMO_CODE,
            "available": True
        })
        user_promo_code_reward_missions_num = len(user_promo_code_reward_missions)
        user_completed_promo_code_reward_missions_num = 0
        total_promo_code_value = 0

        for reward_mission in user_promo_code_reward_missions:
            total_promo_code_value += reward_mission.mission.reward_value
            status = reward_mission.status
            if status == USER_MISSION_STATUS_REWARD_SENT:
                user_completed_promo_code_reward_missions_num += 1
        max_available_promo_code_value = self.user_available_promo_code_value(user_id=user_id)
        used_promo_code_value = self.user_used_promo_code_value(user_id=user_id)
        available_promo_code_value = max(max_available_promo_code_value - used_promo_code_value, 0)
        result = {
            "total_promo_code": user_promo_code_reward_missions_num,
            "completed_promo_code_missions": user_completed_promo_code_reward_missions_num,
            "total_promo_code_value": total_promo_code_value,
            "max_available_promo_code_value": max_available_promo_code_value,
            "used_promo_code_value": used_promo_code_value,
            "available_promo_code_value": available_promo_code_value,
        }
        return result

    def update_user_reward_mission(self, user_reward_mission_id: str, user_reward_mission_update_data) \
            -> Optional[UserRewardMission]:
        updated_user_reward_mission = self.user_reward_mission_repository.update_user_reward_mission(
            user_reward_mission_id=user_reward_mission_id,
            user_reward_mission_update_data=user_reward_mission_update_data
        )
        if not updated_user_reward_mission:
            raise UserRewardMissionDoesNotExistException
        return updated_user_reward_mission
