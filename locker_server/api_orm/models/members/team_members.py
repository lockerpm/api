from locker_server.api_orm.abstracts.members.team_members import AbstractTeamMemberORM
from locker_server.shared.constants.members import PM_MEMBER_STATUS_CONFIRMED
from locker_server.shared.utils.app import now


class TeamMemberORM(AbstractTeamMemberORM):
    class Meta(AbstractTeamMemberORM.Meta):
        swappable = 'LS_TEAM_MEMBER_MODEL'
        db_table = 'cs_team_members'

    @classmethod
    def create(cls, team_id: str, role_id: str, is_primary=False, is_default=False,
               status=PM_MEMBER_STATUS_CONFIRMED, user_id: int = None, email: str = None):
        new_member = cls.objects.create(
            user_id=user_id, email=email, role_id=role_id, team_id=team_id, access_time=now(),
            is_primary=is_primary,
            is_default=is_default,
            status=status
        )
        return new_member
