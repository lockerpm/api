from locker_server.api_orm.abstracts.user_rewards.missions import AbstractMissionORM


class MissionORM(AbstractMissionORM):
    class Meta(AbstractMissionORM.Meta):
        swappable = 'LS_MISSION_MODEL'
        db_table = 'cs_missions'
        ordering = ['-order_index']

