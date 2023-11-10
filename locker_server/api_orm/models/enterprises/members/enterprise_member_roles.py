from django.db import models

from locker_server.api_orm.abstracts.enterprises.members.enterprise_member_roles import AbstractEnterpriseMemberRoleORM


class EnterpriseMemberRoleORM(AbstractEnterpriseMemberRoleORM):
    name = models.CharField(primary_key=True, max_length=45)

    class Meta(AbstractEnterpriseMemberRoleORM.Meta):
        swappable = 'LS_ENTERPRISE_MEMBER_ROLE_MODEL'
        db_table = 'e_member_roles'
