from core.repositories import ICollectionRepository

from shared.utils.app import now
from cystack_models.models.teams.teams import Team
from cystack_models.models.teams.collections import Collection


class CollectionRepository(ICollectionRepository):
    def get_team_collection_by_id(self, collection_id: str, team_id: str) -> Collection:
        return Collection.objects.get(team_id=team_id, id=collection_id)

    def get_multiple_team_collections(self, team_id: str):
        return Collection.objects.filter(team_id=team_id).order_by('-creation_date')

    def save_new_collection(self, team: Team, name: str, is_default: bool = False) -> Collection:
        collection = Collection.objects.create(
            team=team, name=name, is_default=is_default,
            creation_date=now(), revision_date=now()
        )
        return collection