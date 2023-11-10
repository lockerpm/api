from locker_server.api_orm.abstracts.users.user_score import AbstractUserScoreORM


class UserScoreORM(AbstractUserScoreORM):
    class Meta(AbstractUserScoreORM.Meta):
        db_table = 'cs_user_score'

    @classmethod
    def create(cls, user):
        new_bw_user_score = cls(user=user)
        new_bw_user_score.save()
        return new_bw_user_score
