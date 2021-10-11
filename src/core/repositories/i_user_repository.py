from abc import ABC, abstractmethod
from typing import Dict

from cystack_models.models.users.users import User


class IUserRepository(ABC):
    @abstractmethod
    def retrieve_or_create_by_id(self, user_id, creation_date=None) -> User:
        pass

    @abstractmethod
    def get_by_id(self, user_id) -> User:
        pass

    @abstractmethod
    def get_default_team(self, user: User):
        pass

    @abstractmethod
    def get_by_email(self, email) -> User:
        pass

    @abstractmethod
    def get_kdf_information(self, user) -> Dict:
        pass

    @classmethod
    def get_public_key(cls, user_id) -> str:
        pass

    @abstractmethod
    def get_many_by_ids(self, user_ids: list):
        pass

    @abstractmethod
    def is_activated(self, user: User) -> bool:
        pass

    @abstractmethod
    def retrieve_or_create_user_score(self, user: User):
        pass

    @abstractmethod
    def get_current_plan(self, user: User, scope=None):
        pass

    @abstractmethod
    def get_list_invitations(self, user: User):
        pass

    @abstractmethod
    def delete_account(self, user: User):
        pass

    @abstractmethod
    def purge_account(self, user: User):
        pass

    @abstractmethod
    def revoke_all_sessions(self, user: User):
        pass

    @abstractmethod
    def change_master_password_hash(self, user: User, new_master_password_hash: str, key: str):
        pass
