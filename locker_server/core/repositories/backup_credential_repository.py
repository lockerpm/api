from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.user.backup_credential import BackupCredential


class BackupCredentialRepository(ABC):
    # ------------------------ List BackupCredential resource ------------------- #
    @abstractmethod
    def list_backup_credentials(self, **filters) -> [BackupCredential]:
        pass

    @abstractmethod
    def count_backup_credentials(self, **filters) -> int:
        pass

    # ------------------------ Get BackupCredential resource --------------------- #
    @abstractmethod
    def get_by_id(self, backup_credential_id: str) -> Optional[BackupCredential]:
        pass

    # ------------------------ Create BackupCredential resource --------------------- #
    @abstractmethod
    def create_backup_credential(self, backup_credential_create_data: Dict) -> Optional[BackupCredential]:
        pass

    # ------------------------ Update BackupCredential resource --------------------- #

    # ------------------------ Delete BackupCredential resource --------------------- #
    @abstractmethod
    def delete_backup_credential(self, backup_credential_id: str) -> bool:
        pass
