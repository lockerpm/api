from core.repositories import IGroupRepository
from core.utils.account_revision_date import bump_account_revision_date

from shared.utils.app import now, diff_list
from cystack_models.models.teams.teams import Team
from cystack_models.models.teams.groups import Group


class GroupRepository(IGroupRepository):
    def get_multiple_by_team_id(self, team_id):
        return Group.objects.filter(team_id=team_id).order_by('-creation_date')

    def get_team_group_by_id(self, group_id: str, team_id: str) -> Group:
        return Group.objects.get(id=group_id, team_id=team_id)

    def save_new_group(self, team: Team, name: str, access_all: bool, collections: list) -> Group:
        new_group = Group.create(team=team, name=name, access_all=access_all, collections=collections)
        bump_account_revision_date(team=team)
        return new_group

    def save_update_group(self, group: Group, name: str, access_all: bool, collections: list) -> Group:
        group.name = name
        group.access_all = access_all
        group.revision_date = now()
        group.save()
        new_collection_ids = [collection.get("id") for collection in collections]
        existed_collection_ids = list(group.collections_groups.values_list('collection_id', flat=True))
        removed_collection_ids = diff_list(existed_collection_ids, new_collection_ids)
        added_collection_ids = diff_list(new_collection_ids, new_collection_ids)
        if removed_collection_ids:
            group.collections_groups.filter(
                collection_id__in=removed_collection_ids
            ).order_by('-collection_id').delete()
        if added_collection_ids:
            new_collections = [collection for collection in collections if collection.get("id") in added_collection_ids]
            group.collections_groups.model.create_multiple_by_group(group, *new_collections)
        bump_account_revision_date(team=group.team)
        return group

    def save_update_user_group(self, group: Group, member_ids: list) -> Group:
        group.groups_members.all().delete()
        group.groups_members.model.create_multiple(group, *member_ids)
        return group
