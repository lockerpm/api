from locker_server.api_orm.model_parsers.wrapper_specific_model_parser import get_specific_model_parser
from locker_server.api_orm.models import UserRewardMissionORM, MissionORM, PromoCodeORM, PromoCodeTypeORM
from locker_server.core.entities.payment.promo_code import PromoCode
from locker_server.core.entities.payment.promo_code_type import PromoCodeType
from locker_server.core.entities.user_reward.mission import Mission
from locker_server.core.entities.user_reward.user_reward_mission import UserRewardMission


class UserRewardParser:
    @classmethod
    def parse_user_reward_mission(cls, user_reward_mission_orm: UserRewardMissionORM) -> UserRewardMission:
        user_parser = get_specific_model_parser("UserParser")

        return UserRewardMission(
            user_reward_mission_id=user_reward_mission_orm.id,
            user=user_parser.parse_user(user_orm=user_reward_mission_orm.user),
            mission=cls.parse_mission(mission_orm=user_reward_mission_orm.mission),
            status=user_reward_mission_orm.status,
            is_claimed=user_reward_mission_orm.is_claimed,
            completed_time=user_reward_mission_orm.completed_time,
            answer=user_reward_mission_orm.answer,
        )

    @classmethod
    def parse_mission(cls, mission_orm: MissionORM) -> Mission:
        return Mission(
            mission_id=mission_orm.id,
            title=mission_orm.title,
            description_en=mission_orm.description_en,
            description_vi=mission_orm.description_vi,
            created_time=mission_orm.created_time,
            mission_type=mission_orm.mission_type,
            order_index=mission_orm.order_index,
            available=mission_orm.available,
            extra_requirements=mission_orm.extra_requirements,
            reward_type=mission_orm.reward_type,
            reward_value=mission_orm.reward_value,
        )
