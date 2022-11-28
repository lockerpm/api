from abc import ABC, abstractmethod
from typing import Dict

from shared.constants.transactions import DURATION_MONTHLY
from cystack_models.models.users.users import User


class IUserRepository(ABC):
    @abstractmethod
    def list_users(self, **filter_params):
        pass

    @abstractmethod
    def retrieve_or_create_by_id(self, user_id, creation_date=None) -> User:
        pass

    @abstractmethod
    def upgrade_member_family_plan(self, user):
        pass

    @abstractmethod
    def invitations_confirm(self, user):
        pass

    @abstractmethod
    def sharing_invitations_confirm(self, user, email: str = None):
        pass

    @abstractmethod
    def enterprise_invitations_confirm(self, user, email: str = None):
        pass

    @abstractmethod
    def enterprise_share_groups_confirm(self, user, email: str = None):
        pass

    @abstractmethod
    def get_by_id(self, user_id) -> User:
        pass

    @abstractmethod
    def get_default_team(self, user: User):
        pass

    @abstractmethod
    def get_default_enterprise(self, user: User, enterprise_name: str = None, create_if_not_exist=False):
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
    def get_user_type(self, user_id: int) -> str:
        pass

    @abstractmethod
    def retrieve_or_create_user_score(self, user: User):
        pass

    @abstractmethod
    def get_personal_team_plans(self, user: User):
        pass

    @abstractmethod
    def get_max_allow_cipher_type(self, user: User):
        pass

    @abstractmethod
    def get_mobile_user_plan(self, pm_mobile_subscription):
        pass

    @abstractmethod
    def get_current_plan(self, user: User, scope=None):
        pass

    @abstractmethod
    def update_plan(self, user: User, plan_type_alias: str, duration=DURATION_MONTHLY, scope=None, **kwargs):
        pass

    @abstractmethod
    def cancel_plan(self, user: User, scope=None, immediately=False):
        pass

    @abstractmethod
    def add_to_family_sharing(self, family_user_plan, user_id: int = None, email: str = None):
        pass

    @abstractmethod
    def get_max_allow_member_pm_team(self, user: User, scope=None):
        pass

    @abstractmethod
    def get_customer_data(self, user: User, token_card=None, id_card=None):
        pass

    @abstractmethod
    def get_list_invitations(self, user: User, personal_share=False):
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
