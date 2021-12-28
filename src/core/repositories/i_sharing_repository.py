from abc import ABC, abstractmethod

from cystack_models.models.ciphers.ciphers import Cipher


class ISharingRepository(ABC):
    @abstractmethod
    def create_new_sharing(self, sharing_key: str, members, cipher=None,
                           folder=None, shared_collection_name: str = None):
        pass
