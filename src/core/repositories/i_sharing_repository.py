from abc import ABC, abstractmethod

from cystack_models.models.members.team_members import TeamMember


class ISharingRepository(ABC):
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
    def create_new_sharing(self, sharing_key: str, members, cipher=None,
                           folder=None, shared_collection_name: str = None):
        pass
