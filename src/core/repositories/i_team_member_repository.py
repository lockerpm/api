from abc import ABC, abstractmethod

from cystack_models.models.members.team_members import TeamMember


class ITeamMemberRepository(ABC):
    @abstractmethod
    def get_multiple_by_teams(self, teams):
        pass

    @abstractmethod
    def accept_invitation(self, member: TeamMember):
        pass

    @abstractmethod
    def reject_invitation(self, member: TeamMember):
        pass

    @abstractmethod
    def create_invitation_token(self, member: TeamMember) -> str:
        pass