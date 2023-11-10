from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.team.collection import Collection
from locker_server.core.entities.team.group import Group
from locker_server.core.entities.team.group_member import GroupMember
from locker_server.core.entities.team.team import Team


class TeamGroupRepository(ABC):
    # ------------------------ List TeamGroup resource ------------------- #
    @abstractmethod
    def list_groups_by_sharing_id(self, sharing_id: str) -> List[Group]:
        pass

    @abstractmethod
    def list_group_members(self, group_id: str, **filter_params) -> List[GroupMember]:
        pass

    @abstractmethod
    def list_group_members_user_ids(self, group_id: str) -> List[int]:
        pass

    # ------------------------ Get TeamGroup resource --------------------- #
    @abstractmethod
    def get_share_group_by_id(self, sharing_id: str, group_id: str) -> Optional[Group]:
        pass

    @abstractmethod
    def get_share_group_by_enterprise_group_id(self, sharing_id: str, enterprise_group_id: str) -> Optional[Group]:
        pass

    # ------------------------ Create TeamGroup resource --------------------- #

    # ------------------------ Update TeamGroup resource --------------------- #
    @abstractmethod
    def update_group_role_invitation(self, group: Group, role_id: str) -> Optional[Group]:
        pass

    # ------------------------ Delete TeamGroup resource --------------------- #

