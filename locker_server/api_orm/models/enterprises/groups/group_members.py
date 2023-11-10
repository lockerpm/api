from locker_server.api_orm.abstracts.enterprises.groups.group_members import AbstractEnterpriseGroupMemberORM


class EnterpriseGroupMemberORM(AbstractEnterpriseGroupMemberORM):
    class Meta(AbstractEnterpriseGroupMemberORM.Meta):
        swappable = 'LS_ENTERPRISE_GROUP_MEMBER_MODEL'
        db_table = 'e_groups_members'

    @classmethod
    def create_multiple(cls, datas):
        enterprise_group_members_orm = []
        for data in datas:
            enterprise_group_member = cls(
                group_id=data.get("group_id"),
                member_id=data.get("member_id")
            )
            enterprise_group_members_orm.append(enterprise_group_member)
        cls.objects.bulk_create(enterprise_group_members_orm, ignore_conflicts=True, batch_size=100)
