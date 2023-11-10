from django.contrib.auth.hashers import make_password

from locker_server.api_orm.abstracts.users.backup_credential import AbstractBackupCredentialORM
from locker_server.shared.utils.app import now


class BackupCredentialORM(AbstractBackupCredentialORM):
    class Meta(AbstractBackupCredentialORM.Meta):
        swappable = 'LS_BACKUP_CREDENTIAL_MODEL'
        db_table = 'cs_backup_credentials'

    @classmethod
    def create(cls, **data):
        new_backup_credential_orm = cls(
            master_password_hint=data.get("master_password_hint"),
            key=data.get("key"),
            public_key=data.get("public_key"),
            private_key=data.get("private_key"),
            creation_date=data.get("creation_date", now()),
            fd_credential_id=data.get("fd_credential_id"),
            fd_random=data.get("fd_random"),
            user_id=data.get("user_id"),
        )
        raw_master_password = data.get("master_password") or data.get("master_password_hash")
        if raw_master_password is not None:
            new_backup_credential_orm.master_password = make_password(raw_master_password)
        new_backup_credential_orm.save()
        return new_backup_credential_orm
