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

    @abstractmethod
    def save_new_event_by_ciphers(self, ciphers, **data):
        pass

    @abstractmethod
    def normalize_enterprise_activity(self, activity_logs):
        pass

    @abstractmethod
    def export_enterprise_activity(self, enterprise_member, activity_logs, cc_emails=None):
        pass
