from core.repositories import IEventRepository

from cystack_models.models.events.events import Event


class EventRepository(IEventRepository):
    def get_multiple_by_team_id(self, team_id: str):
        return Event.objects.filter(team_id=team_id).order_by('-creation_date')
