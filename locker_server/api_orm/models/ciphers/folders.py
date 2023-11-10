from locker_server.api_orm.abstracts.ciphers.folders import AbstractFolderORM


class FolderORM(AbstractFolderORM):
    class Meta(AbstractFolderORM.Meta):
        swappable = 'LS_FOLDER_MODEL'
        db_table = 'cs_folders'
