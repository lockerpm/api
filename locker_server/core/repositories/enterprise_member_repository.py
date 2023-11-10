from typing import Union, Dict, Optional, List, NoReturn
from abc import ABC, abstractmethod

from locker_server.core.entities.enterprise.member.enterprise_member import EnterpriseMember
from locker_server.core.entities.user.user import User


class EnterpriseMemberRepository(ABC):
    # ------------------------ List EnterpriseMember resource ------------------- #
    @abstractmethod
    def list_enterprise_members(self, **filters) -> List[EnterpriseMember]:
        pass

    @abstractmethod
    def list_enterprise_member_user_id_by_roles(self, enterprise_id: str, role_ids: List[str]) -> List[str]:
        pass

    @abstractmethod
    def list_enterprise_member_user_id_by_members(self, enterprise_id: str, member_ids: List[str]) -> List[str]:
        pass

    @abstractmethod
    def list_enterprise_member_user_ids(self, **filter_params) -> List[int]:
        pass

    @abstractmethod
    def list_enterprise_members_by_emails(self, emails_param: [str]) -> List[EnterpriseMember]:
        pass

    @abstractmethod
    def count_enterprise_members(self, **filters) -> int:
        pass

    # ------------------------ Get EnterpriseMember resource --------------------- #
    @abstractmethod
    def get_primary_member(self, enterprise_id: str) -> Optional[EnterpriseMember]:
        pass

    @abstractmethod
    def get_enterprise_member_by_id(self, member_id: str) -> Optional[EnterpriseMember]:
        pass

    @abstractmethod
    def get_enterprise_member_by_user_id(self, enterprise_id: str, user_id: int) -> Optional[EnterpriseMember]:
        pass

    @abstractmethod
    def get_enterprise_member_by_token(self, token: str) -> Optional[EnterpriseMember]:
        pass

    @abstractmethod
    def lock_login_account_belong_enterprise(self, user_id: int) -> bool:
        pass

    @abstractmethod
    def is_active_enterprise_member(self, user_id: int) -> bool:
        pass

    @abstractmethod
    def is_in_enterprise(self, user_id: int, enterprise_locked: bool = None) -> bool:
        pass

    # ------------------------ Create EnterpriseMember resource --------------------- #
    @abstractmethod
    def create_member(self, member_create_data: Dict) -> EnterpriseMember:
        pass

    @abstractmethod
    def create_multiple_member(self, members_create_data: [Dict]) -> int:
        pass

    # ------------------------ Update EnterpriseMember resource --------------------- #
    @abstractmethod
    def enterprise_invitations_confirm(self, user: User, email: str = None) -> Optional[User]:
        pass

    @abstractmethod
    def enterprise_share_groups_confirm(self, user: User) -> Optional[User]:
        pass

    @abstractmethod
    def update_enterprise_member(self, enterprise_member_id: str, enterprise_member_update_data: Dict) \
            -> Optional[EnterpriseMember]:
        pass

    @abstractmethod
    def update_batch_enterprise_members(self, enterprise_member_ids: List[str], **enterprise_member_update_data):
        pass

    @abstractmethod
    def update_batch_enterprise_members_by_user_ids(self, user_ids: List[str], **enterprise_member_update_data) -> int:
        pass

    # ------------------------ Delete EnterpriseMember resource --------------------- #
    @abstractmethod
    def delete_enterprise_member(self, enterprise_member_id: str) -> bool:
        pass
