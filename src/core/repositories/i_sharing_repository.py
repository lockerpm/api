from abc import ABC, abstractmethod

from cystack_models.models.members.team_members import TeamMember


class ISharingRepository(ABC):
    @abstractmethod
    def get_personal_share_type(self, member: TeamMember):
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
    def stop_share(self, member: TeamMember,
                   cipher=None, cipher_data=None,
                   collection=None, personal_folder_name: str = None, personal_folder_ciphers=None):
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
    def get_my_personal_shared_teams(self, user):
        pass

    @abstractmethod
    def get_shared_members(self, personal_share_team, exclude_owner=True):
        pass
