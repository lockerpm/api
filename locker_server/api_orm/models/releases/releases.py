from locker_server.api_orm.abstracts.releases.releases import AbstractReleaseORM


class ReleaseORM(AbstractReleaseORM):
    class Meta(AbstractReleaseORM.Meta):
        swappable = 'LS_RELEASE_MODEL'
        db_table = 'cs_releases'
