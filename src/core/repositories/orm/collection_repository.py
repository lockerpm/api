from django.db.models import Q, Value, BooleanField, Case, When

from core.repositories import ICollectionRepository
from core.utils.account_revision_date import bump_account_revision_date

from shared.utils.app import now
from shared.constants.members import *
from cystack_models.models.users.users import User
from cystack_models.models.teams.teams import Team
from cystack_models.models.teams.collections import Collection
from cystack_models.models.teams.collections_members import CollectionMember


class CollectionRepository(ICollectionRepository):
    def get_team_collection_by_id(self, collection_id: str, team_id: str) -> Collection:
        return Collection.objects.get(team_id=team_id, id=collection_id)

    def get_multiple_team_collections(self, team_id: str):
        return Collection.objects.filter(team_id=team_id).order_by('-creation_date')

    def get_multiple_user_collections(self, user: User, exclude_team_ids=None, filter_ids=None):
        members = user.team_members.filter(status=PM_MEMBER_STATUS_CONFIRMED, team__key__isnull=False)
        if exclude_team_ids and isinstance(exclude_team_ids, list):
            members = members.exclude(team_id__in=exclude_team_ids)

        # Collections that user is an owner or admin or user belongs to a group that can access all.
        access_all_teams = list(members.filter(
            Q(role__name__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]) |
            Q(team__groups__access_all=True, team__groups__groups_members__member__user=user)
        ).values_list('team_id', flat=True))
        access_all_collections = Collection.objects.filter(team_id__in=access_all_teams)

        limit_members = members.filter(role__name__in=[MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER])
        collection_members = CollectionMember.objects.filter(member__in=limit_members)
        hide_password_collection_ids = list(
            collection_members.filter(hide_passwords=True).values_list('collection_id', flat=True)
        )
        collection_members_ids = list(collection_members.values_list('collection_id', flat=True))
        # collection_groups_ids = list(CollectionGroup.objects.filter(
        #     group_id__in=GroupMember.objects.filter(member__in=limit_members).values_list('group_id', flat=True)
        # ).values_list('collection_id', flat=True))
        # limit_collections = Collection.objects.filter(id__in=collection_members_ids + collection_groups_ids)
        limit_collections = Collection.objects.filter(id__in=collection_members_ids)

        collections = (access_all_collections | limit_collections).distinct()
        if filter_ids:
            collections = collections.filter(id__in=filter_ids)
        collections = collections.annotate(
            hide_passwords=Case(
                When(id__in=hide_password_collection_ids, then=True),
                default=False,
                output_field=BooleanField()
            )
        ).order_by('-creation_date')
        return collections

    def save_new_collection(self, team: Team, name: str, is_default: bool = False) -> Collection:
        collection = Collection.objects.create(
            team=team, name=name, is_default=is_default,
            creation_date=now(), revision_date=now()
        )
        bump_account_revision_date(team=team)
        return collection

    def save_update_collection(self, collection: Collection, name: str, groups=None) -> Collection:
        collection.name = name
        collection.revision_date = now()
        collection.save()
        # if groups:
        #     collection.collections_groups.all().delete()
        #     groups_data = [{"id": group_id} for group_id in groups]
        #     collection.collections_groups.model.create_multiple(collection, *groups_data)
        bump_account_revision_date(team=collection.team)
        return collection

    def save_update_user_collection(self, collection: Collection, *users) -> Collection:
        collection.collections_members.all().delete()
        members_data = [{
            "id": member.get("id"),
            "role": member.get("role"),
            "hide_passwords": False,
            "read_only": True if member.get("role") == MEMBER_ROLE_MEMBER else False,
        } for member in users]
        collection.collections_members.model.create_multiple_by_collection(collection, *members_data)
        return collection

    def destroy_collection(self, collection: Collection):
        team = collection.team
        collection.delete()
        bump_account_revision_date(team=team)
