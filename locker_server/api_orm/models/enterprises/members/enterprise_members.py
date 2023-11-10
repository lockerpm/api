from locker_server.api_orm.abstracts.enterprises.members.enterprise_members import AbstractEnterpriseMemberORM
from locker_server.shared.constants.enterprise_members import E_MEMBER_STATUS_INVITED
from locker_server.shared.utils.app import now


class EnterpriseMemberORM(AbstractEnterpriseMemberORM):
    class Meta(AbstractEnterpriseMemberORM.Meta):
        swappable = 'LS_ENTERPRISE_MEMBER_MODEL'
        db_table = 'e_members'

    @classmethod
    def create_member(cls, **data):
        member_orm = cls(
            enterprise_id=data.get("enterprise_id"),
            user_id=data.get("user_id"),
            role_id=data.get("role_id") or data.get("role"),
            status=data.get("status", E_MEMBER_STATUS_INVITED),
            is_primary=data.get("is_primary", False),
            is_default=data.get("is_default", False),
            token_invitation=data.get("token_invitation", None),
            access_time=now(),
            email=data.get("email", None),
        )
        member_orm.save()
        return member_orm

    @classmethod
    def create_multiple_member(cls, datas):
        enterprises_orm = []
        for data in datas:
            enterprise_orm = cls(
                enterprise_id=data.get("enterprise_id"),
                user_id=data.get("user_id"),
                role_id=data.get("role") or data.get("role_id"),
                domain_id=data.get("domain_id"),
                status=data.get("status", E_MEMBER_STATUS_INVITED),
                is_primary=data.get("is_primary", False),
                is_default=data.get("is_default", False),
                access_time=data.get("access_time") or now(),
                email=data.get("email", None),
                token_invitation=data.get("token_invitation", None),

            )
            enterprises_orm.append(enterprise_orm)
        new_members_obj = cls.objects.bulk_create(enterprises_orm, ignore_conflicts=True, batch_size=100)
        return len(new_members_obj)
