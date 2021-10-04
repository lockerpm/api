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
    def save_new_cipher(self, cipher_data):
        pass

    @abstractmethod
    def save_update_cipher(self, cipher_data):
        pass
