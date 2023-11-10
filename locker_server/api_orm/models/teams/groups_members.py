from locker_server.api_orm.abstracts.teams.groups_members import AbstractGroupMemberORM


class GroupMemberORM(AbstractGroupMemberORM):
    class Meta(AbstractGroupMemberORM.Meta):
        swappable = 'LS_GROUP_MEMBER_MODEL'
        db_table = 'cs_groups_members'
