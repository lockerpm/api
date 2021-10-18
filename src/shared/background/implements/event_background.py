from django.db import connection

from core.settings import CORE_CONFIG
from shared.background.i_background import ILockerBackground


class EventBackground(ILockerBackground):
    event_repository = CORE_CONFIG["repositories"]["IEventRepository"]()

    def create(self, **data):
        try:
            self.event_repository.save_new_event(**data)
        except Exception as e:
            self.log_error(func_name="create")
        finally:
            if self.background:
                connection.close()

    def create_by_team_ids(self, team_ids, **data):
        try:
            if team_ids:
                self.event_repository.save_new_event_by_multiple_teams(team_ids, **data)
            else:
                self.create(**data)
        except Exception as e:
            self.log_error(func_name="create_by_team_ids")
        finally:
            if self.background:
                connection.close()
