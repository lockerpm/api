from typing import Optional, List

from django.db.models import Sum

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_user_reward_mission_model
from locker_server.core.entities.user_reward.user_reward_mission import UserRewardMission
from locker_server.core.repositories.user_reward_mission_repository import UserRewardMissionRepository
from locker_server.shared.constants.missions import USER_MISSION_STATUS_REWARD_SENT, REWARD_TYPE_PROMO_CODE

UserRewardMissionORM = get_user_reward_mission_model()
ModelParser = get_model_parser()


class UserRewardMissionORMRepository(UserRewardMissionRepository):

    # ------------------------ List UserRewardMission resource ------------------- #
    def list_user_reward_missions(self, user_id: int, **filters) -> List[UserRewardMission]:
        user_reward_missions_orm = UserRewardMissionORM.objects.filter(
            user_id=user_id
        ).select_related('mission').order_by('mission__order_index')
        available_param = filters.get("available")
        reward_type_param = filters.get("reward_type")
        if available_param is not None:
            user_reward_missions_orm = user_reward_missions_orm.filter(mission__available=available_param)
        if reward_type_param:
            user_reward_missions_orm = user_reward_missions_orm.filter(mission__reward_type=reward_type_param)
        return [
            ModelParser.user_reward_parser().parse_user_reward_mission(user_reward_mission_orm=user_reward_mission_orm)
            for user_reward_mission_orm in user_reward_missions_orm
        ]

    # ------------------------ Get UserRewardMission resource --------------------- #
    def get_user_reward_mission_by_id(self, user_reward_mission_id: str) -> Optional[UserRewardMission]:
        pass

    def get_user_reward_by_mission_id(self, user_id: int, mission_id: str, available: bool = True) \
            -> Optional[UserRewardMission]:
        try:
            user_reward_mission_orm = UserRewardMissionORM.objects.get(
                user_id=user_id,
                mission_id=mission_id,
                mission__available=available
            )
        except UserRewardMissionORM.DoesNotExist:
            return None
        return ModelParser.user_reward_parser().parse_user_reward_mission(
            user_reward_mission_orm=user_reward_mission_orm
        )

    def get_user_available_promo_code_value(self, user_id: int) -> int:
        user_available_promo_code_value = UserRewardMissionORM.objects.filter(
            user_id=user_id, mission__available=True,
            mission__reward_type=REWARD_TYPE_PROMO_CODE,
            status=USER_MISSION_STATUS_REWARD_SENT
        ).aggregate(Sum('mission__reward_value')).get("mission__reward_value__sum") or 0
        return user_available_promo_code_value

    # ------------------------ Create UserRewardMission resource --------------------- #
    def create_user_reward_mission(self, user_reward_mission_create_data) -> Optional[UserRewardMission]:
        pass

    def create_multiple_user_reward_missions(self, user_id: int, mission_ids, **data):
        UserRewardMissionORM.create_multiple_user_reward_missions(
            user_id=user_id,
            mission_ids=mission_ids,
            **data
        )

    # ------------------------ Update UserRewardMission resource --------------------- #

    def update_user_reward_mission(self, user_reward_mission_id: str, user_reward_mission_update_data) \
            -> Optional[UserRewardMission]:
        try:
            user_reward_mission_orm = UserRewardMissionORM.objects.get(id=user_reward_mission_id)
        except UserRewardMissionORM.DoesNotExist:
            return None
        user_reward_mission_orm.answer = user_reward_mission_update_data.get("answer", user_reward_mission_orm.answer)
        user_reward_mission_orm.status = user_reward_mission_update_data.get("status", user_reward_mission_orm.status)
        user_reward_mission_orm.save()
        return ModelParser.user_reward_parser().parse_user_reward_mission(
            user_reward_mission_orm=user_reward_mission_orm
        )

    # ------------------------ Delete UserRewardMission resource --------------------- #
