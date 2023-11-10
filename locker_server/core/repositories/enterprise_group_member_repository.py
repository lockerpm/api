from typing import Union, Dict, Optional, List, NoReturn
from abc import ABC, abstractmethod

from locker_server.core.entities.enterprise.group.group import EnterpriseGroup
from locker_server.core.entities.enterprise.group.group_member import EnterpriseGroupMember


class EnterpriseGroupMemberRepository(ABC):
    # ------------------------ List EnterpriseGroupMember resource ------------------- #
    @abstractmethod
    def list_by_group_id(self, enterprise_group_id: str) -> List[EnterpriseGroupMember]:
        pass

    @abstractmethod
    def list_group_member_user_email(self, enterprise_group_id: str) -> List:
        pass

    @abstractmethod
    def list_enterprise_group_member_user_id_by_id(self, enterprise_id: str, enterprise_group_id: str) -> List[str]:
        pass

    @abstractmethod
    def list_enterprise_group_member_by_member_id(self, enterprise_member_id: str) -> List[EnterpriseGroupMember]:
        pass

    @abstractmethod
    def list_groups_name_by_enterprise_member_id(self, enterprise_member_id: str) -> List[str]:
        pass

    @abstractmethod
    def list_enterprise_group_members(self, **filters) -> List[EnterpriseGroupMember]:
        pass

    @abstractmethod
    def count_enterprise_group_members(self, enterprise_group_id) -> int:
        pass

    # ------------------------ Get EnterpriseGroupMember resource --------------------- #

    # ------------------------ Create EnterpriseGroupMember resource --------------------- #
    @abstractmethod
    def create_multiple_group_member(self, group_members_create_data: [Dict]) -> NoReturn:
        pass

    # ------------------------ Update EnterpriseGroupMember resource --------------------- #

    # ------------------------ Delete EnterpriseGroupMember resource --------------------- #
    @abstractmethod
    def delete_group_members_by_member_id(self, enterprise_member_id: str) -> bool:
        pass

    @abstractmethod
    def delete_multiple_by_member_ids(self, enterprise_group: EnterpriseGroup, deleted_member_ids: [str]) -> List[int]:
        pass
