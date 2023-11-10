from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.cipher.cipher import Cipher
from locker_server.core.entities.cipher.folder import Folder
from locker_server.core.entities.enterprise.group.group import EnterpriseGroup
from locker_server.core.entities.member.team_member import TeamMember
from locker_server.core.entities.team.collection import Collection
from locker_server.core.entities.team.group import Group
from locker_server.core.entities.team.team import Team


class SharingRepository(ABC):
    # ------------------------ List Sharing resource ------------------- #
    @abstractmethod
    def list_sharing_invitations(self, user_id: int, personal_share: bool = True) -> List[TeamMember]:
        pass

    @abstractmethod
    def list_my_personal_share_teams(self, user_id: int, **filter_params) -> List[Team]:
        pass

    # ------------------------ Get Sharing resource --------------------- #
    @abstractmethod
    def get_shared_members(self, personal_shared_team: Team,
                           exclude_owner=True, is_added_by_group=None) -> List[TeamMember]:
        pass

    @abstractmethod
    def get_share_cipher(self, sharing_id: str) -> Optional[Cipher]:
        pass

    @abstractmethod
    def get_sharing_cipher_type(self, sharing_id: str) -> Union[str, int]:
        pass

    @abstractmethod
    def get_share_collection(self, sharing_id: str) -> Optional[Collection]:
        pass

    # ------------------------ Create Sharing resource --------------------- #
    @abstractmethod
    def create_new_sharing(self, sharing_key: str, members, groups=None,
                           cipher: Cipher = None, shared_cipher_data=None,
                           folder: Folder = None, shared_collection_name: str = None, shared_collection_ciphers=None):
        pass

    # ------------------------ Update Sharing resource --------------------- #
    @abstractmethod
    def accept_invitation(self, member: TeamMember) -> Optional[TeamMember]:
        pass

    @abstractmethod
    def reject_invitation(self, member: TeamMember):
        pass

    @abstractmethod
    def confirm_invitation(self, member: TeamMember, key: str):
        pass

    @abstractmethod
    def update_role_invitation(self, member: TeamMember, role_id: str,
                               hide_passwords: bool = None) -> Optional[TeamMember]:
        pass

    @abstractmethod
    def add_members(self, team_id: str, shared_collection_id: str, members: List, groups: List = None):
        pass

    @abstractmethod
    def add_group_members(self, team_id: str, shared_collection_id: str, groups):
        pass

    @abstractmethod
    def stop_sharing(self, member: TeamMember = None, group: Group = None,
                     cipher: Cipher = None, cipher_data=None,
                     collection: Collection = None, personal_folder_name: str = None, personal_folder_ciphers=None):
        pass

    @abstractmethod
    def stop_share_all_members(self, team_id: str, cipher=None, cipher_data=None,
                               collection=None, personal_folder_name: str = None, personal_folder_ciphers=None):
        pass

    @abstractmethod
    def leave_sharing(self, member: TeamMember) -> int:
        pass

    @abstractmethod
    def update_share_folder(self, collection: Collection, name: str, groups=None, revision_date=None) -> Collection:
        pass

    @abstractmethod
    def delete_share_folder(self, collection: Collection,
                            personal_folder_name: str = None, personal_folder_ciphers=None):
        pass

    @abstractmethod
    def add_group_member_to_share(self, enterprise_group: EnterpriseGroup, new_member_ids: List[str]):
        pass

    # ------------------------ Delete Sharing resource --------------------- #

