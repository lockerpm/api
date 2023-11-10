from django.db.models import Count

from locker_server.api_orm.abstracts.enterprises.groups.groups import AbstractEnterpriseGroupORM
from locker_server.shared.constants.members import MEMBER_ROLE_OWNER
from locker_server.shared.utils.app import now


class EnterpriseGroupORM(AbstractEnterpriseGroupORM):
    class Meta(AbstractEnterpriseGroupORM.Meta):
        swappable = 'LS_ENTERPRISE_GROUP_MODEL'
        db_table = 'e_enterprise_groups'


    @classmethod
    def create(cls, **data):
        enterprise_group_orm = cls(
            name=data.get("name"),
            enterprise_id=data.get("enterprise_id"),
            created_by_id=data.get("created_by_id"),
            creation_date=data.get("creation_date", now()),
            revision_date=data.get("revision_date")
        )
        enterprise_group_orm.save()
        return enterprise_group_orm
