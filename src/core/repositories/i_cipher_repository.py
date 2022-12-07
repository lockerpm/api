from abc import ABC, abstractmethod

from cystack_models.models.ciphers.ciphers import Cipher


class ICipherRepository(ABC):
    @abstractmethod
    def get_by_id(self, cipher_id: str) -> Cipher:
        pass

    @abstractmethod
    def get_cipher_members(self, cipher):
        pass

    @abstractmethod
    def get_multiple_by_ids(self, cipher_ids: list):
        pass

    @abstractmethod
    def get_ciphers_created_by_user(self, user):
        pass

    @abstractmethod
    def get_personal_ciphers(self, user):
        pass

    @abstractmethod
    def get_team_ciphers(self, team):
        pass

    @abstractmethod
    def get_multiple_by_user(self, user, only_personal=False, only_managed_team=False,
                             only_edited=False, only_deleted=False,
                             exclude_team_ids=None, filter_ids=None, exclude_types=None):
        pass

    @abstractmethod
    def save_new_cipher(self, cipher_data) -> Cipher:
        pass

    @abstractmethod
    def save_update_cipher(self, cipher: Cipher, cipher_data) -> Cipher:
        pass

    @abstractmethod
    def save_share_cipher(self, cipher: Cipher, cipher_data) -> Cipher:
        pass

    @abstractmethod
    def delete_multiple_cipher(self, cipher_ids, user_deleted):
        pass

    @abstractmethod
    def delete_permanent_multiple_cipher(self, cipher_ids, user_deleted):
        pass

    @abstractmethod
    def delete_permanent_multiple_cipher_by_teams(self, team_ids):
        pass

    @abstractmethod
    def restore_multiple_cipher(self, cipher_ids, user_restored):
        pass

    @abstractmethod
    def move_multiple_cipher(self, cipher_ids, user_moved, folder_id):
        pass

    @abstractmethod
    def import_multiple_cipher(self, user, ciphers, folders, folder_relationships, allow_cipher_type=None):
        pass

    @abstractmethod
    def import_multiple_ciphers(self, user, ciphers, allow_cipher_type=None):
        pass

    @abstractmethod
    def sync_personal_cipher_offline(self, user, ciphers, folders, folder_relationships):
        pass

    @abstractmethod
    def import_multiple_cipher_team(self, team, ciphers, collections, collection_relationships, allow_cipher_type=None):
        pass

