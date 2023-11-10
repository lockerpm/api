from locker_server.api_orm.abstracts.teams.collections_members import AbstractCollectionMemberORM


class CollectionMemberORM(AbstractCollectionMemberORM):
    class Meta(AbstractCollectionMemberORM.Meta):
        swappable = 'LS_COLLECTION_MEMBER_MODEL'
        db_table = 'cs_collections_members'
