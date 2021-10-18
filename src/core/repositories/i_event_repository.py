from abc import ABC, abstractmethod

from cystack_models.models.events.events import Event


class IEventRepository(ABC):
    @abstractmethod
    def get_multiple_by_team_id(self, team_id: str):
        pass

    @abstractmethod
    def save_new_event(self, **data) -> Event:
        pass

    @abstractmethod
    def save_new_event_by_multiple_teams(self, team_ids: list, **data):
        pass
