from typing import Union, Dict
from abc import ABC, abstractmethod

from locker_server.core.entities.user.user import User


class AuthRepository(ABC):
    @abstractmethod
    def decode_token(self, value: str, secret: str) -> Dict:
        pass

    @abstractmethod
    def get_expired_type(self, token_type_name: str) -> Union[int, float]:
        pass

    @abstractmethod
    def check_master_password(self, user: User, raw_password: str) -> bool:
        pass
