from abc import ABC, abstractmethod


class ITeamMemberRepository(ABC):
    @abstractmethod
    def get_multiple_by_teams(self, teams):
        pass
