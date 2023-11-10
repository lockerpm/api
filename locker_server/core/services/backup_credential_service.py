from typing import List, Optional, Dict

from locker_server.core.entities.user.backup_credential import BackupCredential
from locker_server.core.entities.user.user import User
from locker_server.core.exceptions.backup_credential_exception import BackupCredentialDoesNotExistException, \
    BackupCredentialMaximumReachedException
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.core.repositories.backup_credential_repository import BackupCredentialRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.constants.backup_credential import BACKUP_CREDENTIAL_MAX


class BackupCredentialService:
    """
    This class represents Use Cases related User
    """

    def __init__(self, user_repository: UserRepository,
                 backup_credential_repository: BackupCredentialRepository
                 ):
        self.user_repository = user_repository
        self.backup_credential_repository = backup_credential_repository

    def list_backup_credentials(self, **filters) -> List[BackupCredential]:
        return self.backup_credential_repository.list_backup_credentials(**filters)

    def count_backup_credentials(self, **filters) -> int:
        return self.backup_credential_repository.count_backup_credentials(**filters)

    def get_by_id(self, backup_credential_id: [str, int]) -> Optional[BackupCredential]:
        backup_credential = self.backup_credential_repository.get_by_id(
            backup_credential_id=backup_credential_id
        )
        if not backup_credential:
            raise BackupCredentialDoesNotExistException
        return backup_credential

    def create_backup_credential(self, current_user: User, keys: Dict,
                                 backup_credential_create_data: Dict) -> BackupCredential:
        user = self.user_repository.get_user_by_id(user_id=current_user.user_id)
        if not user:
            raise UserDoesNotExistException
        user_backup_credential_num = self.count_backup_credentials(**{
            "user_id": user.user_id
        })
        if user_backup_credential_num >= BACKUP_CREDENTIAL_MAX:
            raise BackupCredentialMaximumReachedException
        backup_credential_create_data.update({
            "user_id": user.user_id,
            "public_key": keys.get("public_key"),
            "private_key": keys.get("encrypted_private_key"),
        })
        return self.backup_credential_repository.create_backup_credential(
            backup_credential_create_data=backup_credential_create_data
        )

    def delete_backup_credential(self, backup_credential_id: str) -> bool:
        deleted_backup_credential = self.backup_credential_repository.delete_backup_credential(
            backup_credential_id=backup_credential_id
        )
        if not deleted_backup_credential:
            raise BackupCredentialDoesNotExistException
        return deleted_backup_credential
