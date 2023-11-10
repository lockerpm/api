from locker_server.api_orm.abstracts.teams.groups import AbstractGroupORM
from locker_server.shared.constants.members import MEMBER_ROLE_MEMBER
from locker_server.shared.utils.app import now


class GroupORM(AbstractGroupORM):
    class Meta(AbstractGroupORM.Meta):
        swappable = 'LS_GROUP_MODEL'
        db_table = 'cs_groups'

    @classmethod
    def retrieve_or_create(cls, team_id, enterprise_group_id, **data):
        group, is_created = cls.objects.get_or_create(
            team_id=team_id, enterprise_group_id=enterprise_group_id, defaults={
                "team_id": team_id,
                "enterprise_group_id": enterprise_group_id,
                "access_all": data.get("access_all", True),
                "creation_date": now(),
                "revision_date": now(),
                "role_id": data.get("role_id", MEMBER_ROLE_MEMBER)
            }
        )
        return group

    @property
    def name(self):
        return self.enterprise_group.name if self.enterprise_group else None
