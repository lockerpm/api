from locker_server.api_orm.abstracts.teams.collections_ciphers import AbstractCollectionCipherORM


class CollectionCipherORM(AbstractCollectionCipherORM):
    class Meta(AbstractCollectionCipherORM.Meta):
        swappable = 'LS_COLLECTION_CIPHER_MODEL'
        db_table = 'cs_collections_ciphers'
