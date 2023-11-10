from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.event.event import Event
from locker_server.core.entities.user.user import User


class EventRepository(ABC):
    # ------------------------ List Event resource ------------------- #
    @abstractmethod
    def list_events(self, **filters) -> List[Event]:
        pass

    @abstractmethod
    def statistic_login_by_time(self, team_id: str, user_ids: List[int], from_param: float, to_param: float) -> Dict:
        pass

    # ------------------------ Get Event resource --------------------- #

    # ------------------------ Create Event resource --------------------- #
    @abstractmethod
    def create_new_event(self, **data) -> Event:
        pass

    @abstractmethod
    def create_new_event_by_multiple_teams(self, team_ids: list, **data):
        pass

    @abstractmethod
    def create_new_event_by_ciphers(self, ciphers, **data):
        pass

    @abstractmethod
    def create_multiple_by_enterprise_members(self, member_events_data):
        pass

    # ------------------------ Update Event resource --------------------- #

    # ------------------------ Delete Event resource --------------------- #
    @abstractmethod
    def delete_old_events(self, creation_date_pivot: float):
        pass
