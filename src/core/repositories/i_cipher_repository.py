from abc import ABC, abstractmethod

from cystack_models.models.ciphers.ciphers import Cipher


class ICipherRepository(ABC):
    @abstractmethod
    def get_favorite_users(self, cipher: Cipher):
        pass

    @abstractmethod
    def get_folder_ids(self, cipher: Cipher):
        pass

    @abstractmethod
    def get_by_id(self, cipher_id: str) -> Cipher:
        pass

    @abstractmethod
    def get_multiple_by_ids(self, cipher_ids: list):
        pass

    @abstractmethod
    def get_multiple_by_user(self, user, only_personal=False):
        pass

    @abstractmethod
    def save_new_cipher(self, cipher_data) -> Cipher:
        pass

    @abstractmethod
    def save_update_cipher(self, cipher: Cipher, cipher_data) -> Cipher:
        pass

    @abstractmethod
    def delete_multiple_cipher(self, cipher_ids, user_deleted):
        pass

    @abstractmethod
    def delete_permanent_multiple_cipher(self, cipher_ids, user_deleted):
        pass

    @abstractmethod
    def restore_multiple_cipher(self, cipher_ids, user_restored):
        pass

    @abstractmethod
    def move_multiple_cipher(self, cipher_ids, user_moved, folder_id):
        pass
