from locker_server.api_orm.abstracts.ciphers.ciphers import AbstractCipherORM


class CipherORM(AbstractCipherORM):
    class Meta(AbstractCipherORM.Meta):
        swappable = 'LS_CIPHER_MODEL'
        db_table = 'cs_ciphers'
