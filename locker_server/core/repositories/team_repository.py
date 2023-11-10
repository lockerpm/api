from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.team.collection import Collection
from locker_server.core.entities.team.team import Team


class TeamRepository(ABC):
    # ------------------------ List Team resource ------------------- #
    @abstractmethod
    def list_team_collection_ids(self, team_id: str) -> List[str]:
        pass

    @abstractmethod
    def list_owner_sharing_ids(self, user_id: int) -> List[str]:
        pass

    # ------------------------ Get Team resource --------------------- #
    @abstractmethod
    def get_by_id(self, team_id: str) -> Optional[Team]:
        pass

    @abstractmethod
    def get_default_collection(self, team_id: str) -> Optional[Collection]:
        pass

    @abstractmethod
    def get_team_collection_by_id(self, team_id: str, collection_id: str) -> Optional[Collection]:
        pass

    # ------------------------ Create Team resource --------------------- #

    # ------------------------ Update Team resource --------------------- #

    # ------------------------ Delete Team resource --------------------- #
    @abstractmethod
    def delete_multiple_teams(self, team_ids: List[str]):
        pass

    @abstractmethod
    def delete_sharing_with_me(self, user_id: int):
        pass
