from abc import ABC, abstractmethod

from cystack_models.models.users.users import User
from cystack_models.models.users.user_refresh_tokens import UserRefreshToken
from cystack_models.models.users.user_access_tokens import UserAccessToken


class ISessionRepository(ABC):
    @abstractmethod
    def fetch_valid_token(self, refresh_token: UserRefreshToken, renew: bool = False) -> UserAccessToken:
        pass

    @abstractmethod
    def get_full_access_token(self, access_token: UserAccessToken) -> str:
        pass

    @abstractmethod
    def filter_refresh_tokens(self, device_identifier: str):
        pass

    @abstractmethod
    def fetch_access_token(self, user: User, renew: bool = False):
        pass
