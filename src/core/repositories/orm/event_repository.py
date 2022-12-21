from typing import List

from core.repositories import IEventRepository

from cystack_models.models.events.events import Event


class EventRepository(IEventRepository):
    def get_multiple_by_team_id(self, team_id: str):
        return Event.objects.filter(team_id=team_id).order_by('-creation_date')

    def save_new_event(self, **data) -> Event:
        return Event.create(**data)

    def save_new_event_by_multiple_teams(self, team_ids: list, **data):
        return Event.create_multiple_by_team_ids(team_ids, **data)

    def save_new_event_by_ciphers(self, ciphers, **data):
        return Event.create_multiple_by_ciphers(ciphers, **data)

    def normalize_enterprise_activity(self, activity_logs: List[Event]):
        pass
