from abc import ABC, abstractmethod

from cystack_models.models.teams.teams import Team
from cystack_models.models.teams.collections import Collection


class ICollectionRepository(ABC):
    @abstractmethod
    def get_team_collection_by_id(self, collection_id: str, team_id: str) -> Collection:
        pass

    @abstractmethod
    def get_multiple_team_collections(self, team_id: str):
        pass

    @abstractmethod
    def save_new_collection(self, team: Team, name: str, is_default: bool = False) -> Collection:
        pass
