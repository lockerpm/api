from abc import ABC, abstractmethod

from cystack_models.models.teams.teams import Team


class ITeamRepository(ABC):
    @abstractmethod
    def is_locked(self, team: Team) -> bool:
        pass

    @abstractmethod
    def is_pwd_team(self, team: Team) -> bool:
        pass

    @abstractmethod
    def get_default_collection(self, team: Team):
        pass

    @abstractmethod
    def get_list_collection_ids(self, team: Team):
        pass

    @abstractmethod
    def get_multiple_team_by_ids(self, team_ids: list):
        pass
