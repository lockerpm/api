from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.cipher.cipher import Cipher
from locker_server.core.entities.cipher.folder import Folder
from locker_server.core.entities.member.team_member import TeamMember
from locker_server.core.entities.user.device import Device
from locker_server.core.entities.user.user import User


class CipherRepository(ABC):
    # ------------------------ List Cipher resource ------------------- #
    @abstractmethod
    def list_cipher_collection_ids(self, cipher_id: str) -> List[str]:
        pass

    @abstractmethod
    def get_multiple_by_user(self, user_id: int, only_personal=False, only_managed_team=False,
                             only_edited=False, only_deleted=False,
                             exclude_team_ids=None, filter_ids=None, exclude_types=None) -> List[Cipher]:
        pass

    @abstractmethod
    def get_ciphers_created_by_user(self, user_id: int) -> List[Cipher]:
        pass

    @abstractmethod
    def get_cipher_ids_created_by_user(self, user_id: int) -> List[str]:
        pass

    @abstractmethod
    def get_multiple_by_ids(self, cipher_ids: List[str]) -> List[Cipher]:
        pass

    @abstractmethod
    def list_cipher_ids_by_folder_id(self, user_id: int, folder_id: str) -> List[str]:
        pass

    @abstractmethod
    def list_cipher_ids_by_collection_id(self, collection_id: str) -> List[str]:
        pass

    # ------------------------ Get Cipher resource --------------------- #
    @abstractmethod
    def get_by_id(self, cipher_id: str) -> Optional[Cipher]:
        pass

    @abstractmethod
    def get_user_folder(self, user_id: int, folder_id: str) -> Optional[Folder]:
        pass

    @abstractmethod
    def count_ciphers_created_by_user(self, user_id: int, **filter_params) -> int:
        pass

    @abstractmethod
    def get_master_pwd_item(self, user_id: int) -> Optional[Cipher]:
        pass

    @abstractmethod
    def check_member_belongs_cipher_collections(self, cipher: Cipher, member: TeamMember) -> bool:
        pass

    @abstractmethod
    def sync_and_statistic_ciphers(self, user_id: int, only_personal=False, only_managed_team=False,
                                   only_edited=False, only_deleted=False,
                                   exclude_team_ids=None, filter_ids=None, exclude_types=None) -> Dict:
        pass

    @abstractmethod
    def statistic_created_ciphers(self, user_id: int) -> Dict:
        pass

    # ------------------------ Create Cipher resource --------------------- #
    @abstractmethod
    def create_cipher(self, cipher_data: Dict) -> Cipher:
        pass

    @abstractmethod
    def sync_personal_cipher_offline(self, user_id: int, ciphers: List, folders: List, folder_relationships: List):
        pass

    @abstractmethod
    def import_multiple_ciphers(self, user: User, ciphers: List, allow_cipher_type: Dict = None):
        pass

    # ------------------------ Update Cipher resource --------------------- #
    @abstractmethod
    def update_cipher(self, cipher_id: str, cipher_data: Dict) -> Cipher:
        pass

    @abstractmethod
    def update_folders(self, cipher_id: str, new_folders_data) -> Cipher:
        pass

    @abstractmethod
    def update_cipher_use(self, cipher_id: str, cipher_use_data: Dict) -> Cipher:
        pass

    @abstractmethod
    def move_multiple_cipher(self, cipher_ids: List[str], user_id_moved: int, folder_id: str) -> List[str]:
        pass

    # ------------------------ Delete Cipher resource --------------------- #
    @abstractmethod
    def delete_permanent_multiple_cipher_by_teams(self, team_ids):
        pass

    @abstractmethod
    def delete_permanent_multiple_cipher(self, cipher_ids: List[str], user_id_deleted: int) -> List[str]:
        pass

    @abstractmethod
    def delete_multiple_cipher(self, cipher_ids: List[str], user_id_deleted: int) -> List[str]:
        pass

    @abstractmethod
    def restore_multiple_cipher(self, cipher_ids: List[str], user_id_restored: int) -> List[str]:
        pass

    @abstractmethod
    def delete_trash_ciphers(self, deleted_date_pivot: float) -> bool:
        pass
