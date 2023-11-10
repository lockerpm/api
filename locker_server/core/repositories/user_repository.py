from typing import Union, Dict, Optional, Tuple, List
from abc import ABC, abstractmethod

from locker_server.core.entities.user.user import User
from locker_server.shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED


class UserRepository(ABC):
    # ------------------------ List User resource ------------------- #
    @abstractmethod
    def list_users(self, **filters) -> List[User]:
        pass

    @abstractmethod
    def list_user_ids(self, **filter_params) -> List[int]:
        pass

    @abstractmethod
    def list_user_emails(self, user_ids: List[int]) -> List[str]:
        pass

    @abstractmethod
    def count_weak_cipher_password(self, user_ids: List[int] = None) -> int:
        pass

    @abstractmethod
    def list_new_users(self) -> List[Dict]:
        pass

    @abstractmethod
    def count_users(self, **filters) -> int:
        pass

    @abstractmethod
    def list_user_ids_tutorial_reminder(self, duration_unit: int) -> Dict:
        pass

    # ------------------------ Get User resource --------------------- #
    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_user_type(self, user_id: int) -> str:
        pass

    @abstractmethod
    def is_in_enterprise(self, user_id: int) -> bool:
        pass

    @abstractmethod
    def is_require_passwordless(self, user_id: int,
                                require_enterprise_member_status: str = E_MEMBER_STATUS_CONFIRMED) -> bool:
        pass

    @abstractmethod
    def is_block_by_2fa_policy(self, user_id: int, is_factor2: bool) -> bool:
        pass

    @abstractmethod
    def count_failed_login_event(self, user_id: int) -> int:
        pass

    @abstractmethod
    def has_master_pw_item(self, user_id: int) -> bool:
        pass

    @abstractmethod
    def get_from_cystack_id(self, user_id: int) -> Dict:
        pass

    @abstractmethod
    def get_user_cipher_overview(self, user_id: int) -> Dict:
        pass

    @abstractmethod
    def get_customer_data(self, user: User, token_card=None, id_card=None) -> Dict:
        pass

    @abstractmethod
    def allow_create_enterprise_user(self) -> bool:
        pass

    @abstractmethod
    def check_exist(self) -> bool:
        pass

    # ------------------------ Create User resource --------------------- #
    @abstractmethod
    def retrieve_or_create_by_id(self, user_id, creation_date=None) -> Tuple[User, bool]:
        pass

    @abstractmethod
    def retrieve_or_create_by_email(self, email: str, creation_date=None) -> Tuple[User, bool]:
        pass

    # ------------------------ Update User resource --------------------- #
    @abstractmethod
    def update_user(self, user_id: int, user_update_data) -> Optional[User]:
        pass

    @abstractmethod
    def update_login_time_user(self, user_id: int, update_data) -> Optional[User]:
        pass

    @abstractmethod
    def update_passwordless_cred(self, user_id: int, fd_credential_id: str, fd_random: str) -> User:
        pass

    @abstractmethod
    def change_master_password(self, user: User, new_master_password_hash: str, new_master_password_hint: str = None,
                               key: str = None, score=None, login_method: str = None):
        pass

    @abstractmethod
    def update_user_factor2(self, user_id: int, is_factor2: bool) -> Optional[User]:
        pass

    # ------------------------ Delete User resource --------------------- #
    @abstractmethod
    def purge_account(self, user: User):
        pass

    @abstractmethod
    def delete_account(self, user: User):
        pass

    @abstractmethod
    def revoke_all_sessions(self, user: User, exclude_sso_token_ids=None) -> User:
        pass

    @abstractmethod
    def delete_sync_cache_data(self, user_id: int):
        pass
