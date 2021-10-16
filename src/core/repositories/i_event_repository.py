from abc import ABC, abstractmethod

from cystack_models.models.teams.teams import Team


class IEventRepository(ABC):
    @abstractmethod
    def get_multiple_by_team_id(self, team_id: str):
        pass
