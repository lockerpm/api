from locker_server.api_orm.abstracts.user_rewards.user_reward_missions import AbstractUserRewardMissionORM
from locker_server.shared.constants.missions import USER_MISSION_STATUS_NOT_STARTED


class UserRewardMissionORM(AbstractUserRewardMissionORM):
    class Meta(AbstractUserRewardMissionORM.Meta):
        db_table = 'cs_user_reward_missions'

    @classmethod
    def create_multiple_user_reward_missions(cls, user_id: int, mission_ids, **data):
        user_reward_mission_objs = []
        for mission_id in mission_ids:
            user_reward_mission_objs.append(cls(
                user_id=user_id,
                mission_id=mission_id,
                status=data.get("status", USER_MISSION_STATUS_NOT_STARTED),
                is_claimed=data.get("is_claimed", False),
                completed_time=data.get("completed")
            ))
        cls.objects.bulk_create(user_reward_mission_objs, ignore_conflicts=True, batch_size=50)
