from abc import ABC, abstractmethod

from cystack_models.models.teams.teams import Team
from cystack_models.models.users.users import User
from cystack_models.models.teams.collections import Collection


class ICollectionRepository(ABC):
    @abstractmethod
    def get_team_collection_by_id(self, collection_id: str, team_id: str) -> Collection:
        pass

    @abstractmethod
    def get_multiple_team_collections(self, team_id: str):
        pass

    @abstractmethod
    def get_multiple_user_collections(self, user: User, exclude_team_ids=None, filter_ids=None):
        pass

    @abstractmethod
    def save_new_collection(self, team: Team, name: str, is_default: bool = False) -> Collection:
        pass

    @abstractmethod
    def save_update_collection(self, collection: Collection, name: str, *groups) -> Collection:
        pass

    @abstractmethod
    def save_update_user_collection(self, collection: Collection, *users):
        pass

    @abstractmethod
    def destroy_collection(self, collection: Collection):
        pass

