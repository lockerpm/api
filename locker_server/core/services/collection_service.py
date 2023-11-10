from typing import List, Optional

from locker_server.core.entities.team.collection import Collection
from locker_server.core.exceptions.collection_exception import CollectionDoesNotExistException
from locker_server.core.repositories.collection_repository import CollectionRepository


class CollectionService:
    """
    This class represents Use Cases related Collection
    """

    def __init__(self, collection_repository: CollectionRepository):
        self.collection_repository = collection_repository

    def list_user_collections(self, user_id: int, exclude_team_ids=None, filter_ids=None) -> List[Collection]:
        return self.collection_repository.list_user_collections(
            user_id=user_id, exclude_team_ids=exclude_team_ids, filter_ids=filter_ids
        )

    def get_collection_by_id(self, collection_id: str) -> Optional[Collection]:
        collection = self.collection_repository.get_by_id(collection_id=collection_id)
        if not collection:
            raise CollectionDoesNotExistException
        return collection
