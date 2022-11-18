from abc import ABC, abstractmethod

from cystack_models.models.members.team_members import TeamMember
from cystack_models.models.teams.groups import Group


class ISharingRepository(ABC):
    @abstractmethod
    def get_personal_share_type(self, member: TeamMember):
        pass

    @abstractmethod
    def get_share_type(self, role_id: str):
        pass

    @abstractmethod
    def accept_invitation(self, member: TeamMember):
        pass

    @abstractmethod
    def reject_invitation(self, member: TeamMember):
        pass

    @abstractmethod
    def confirm_invitation(self, member: TeamMember, key: str):
        pass

    @abstractmethod
    def update_role_invitation(self, member: TeamMember, role_id: str, hide_passwords: bool = None):
        pass

    @abstractmethod
    def update_group_role_invitation(self, group: Group, role_id: str):
        pass

    @abstractmethod
    def stop_share_all_members(self, team, cipher=None, cipher_data=None,
                               collection=None, personal_folder_name: str = None, personal_folder_ciphers=None):
        pass

    @abstractmethod
    def stop_share(self, member: TeamMember = None, group: Group = None,
                   cipher=None, cipher_data=None,
                   collection=None, personal_folder_name: str = None, personal_folder_ciphers=None):
        pass

    @abstractmethod
    def delete_share_folder(self, team, collection=None, personal_folder_name: str = None, personal_folder_ciphers=None):
        pass

    @abstractmethod
    def leave_share(self, member: TeamMember):
        pass

    @abstractmethod
    def create_new_sharing(self, sharing_key: str, members,
                           cipher=None, shared_cipher_data=None,
                           folder=None, shared_collection_name: str = None, shared_collection_ciphers=None):
        pass

    @abstractmethod
    def add_members(self, team, shared_collection, members):
        pass

    @abstractmethod
    def add_group_members(self, team, shared_collection, groups):
        pass

    @abstractmethod
    def get_my_personal_shared_teams(self, user):
        pass

    @abstractmethod
    def get_shared_members(self, personal_share_team, exclude_owner=True, is_added_by_group=None):
        pass

    @abstractmethod
    def get_shared_groups(self, personal_share_team):
        pass

    @abstractmethod
    def delete_share_with_me(self, user):
        pass

