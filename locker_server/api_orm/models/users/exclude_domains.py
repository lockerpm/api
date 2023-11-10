from locker_server.api_orm.abstracts.users.exclude_domains import AbstractExcludeDomainORM


class ExcludeDomainORM(AbstractExcludeDomainORM):
    class Meta(AbstractExcludeDomainORM.Meta):
        db_table = 'cs_exclude_domains'
