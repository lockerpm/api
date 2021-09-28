from abc import ABC, abstractmethod
from typing import Dict

from cystack_models.models.users.users import User


class IUserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id) -> User:
        pass

    @abstractmethod
    def get_by_email(self, email) -> User:
        pass

    @abstractmethod
    def get_kdf_information_by_email(self, email) -> Dict:
        pass

    @classmethod
    def get_public_key(cls, user_id) -> str:
        pass

    @abstractmethod
    def get_many_by_ids(self, user_ids: list):
        pass
