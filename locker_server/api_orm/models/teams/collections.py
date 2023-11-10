from locker_server.api_orm.abstracts.teams.collections import AbstractCollectionORM


class CollectionORM(AbstractCollectionORM):
    class Meta(AbstractCollectionORM.Meta):
        swappable = 'LS_COLLECTION_MODEL'
        db_table = 'cs_collections'

