from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from django.db.models import Q, Case, When, BooleanField

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_team_member_model, get_collection_model, \
    get_collection_member_model
from locker_server.core.entities.cipher.cipher import Cipher
from locker_server.core.entities.cipher.folder import Folder
from locker_server.core.entities.member.team_member import TeamMember
from locker_server.core.entities.team.collection import Collection
from locker_server.core.entities.user.device import Device
from locker_server.core.entities.user.user import User
from locker_server.core.repositories.collection_repository import CollectionRepository
from locker_server.shared.constants.members import *


CollectionORM = get_collection_model()
CollectionMemberORM = get_collection_member_model()
TeamMemberORM = get_team_member_model()
ModelParser = get_model_parser()


class CollectionORMRepository(CollectionRepository):
    # ------------------------ List Collection resource ------------------- #
    def list_user_collections(self, user_id: int, exclude_team_ids=None, filter_ids=None) -> List[Collection]:
        members_orm = TeamMemberORM.objects.filter(
            user_id=user_id, status=PM_MEMBER_STATUS_CONFIRMED, team__key__isnull=False
        )
        if exclude_team_ids and isinstance(exclude_team_ids, list):
            members_orm = members_orm.exclude(team_id__in=exclude_team_ids)

        # Collections that user is an owner or admin or user belongs to a group that can access all.
        access_all_teams_orm = list(members_orm.filter(
            Q(role_id__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]) |
            Q(team__groups__access_all=True, team__groups__groups_members__member__user_id=user_id)
        ).values_list('team_id', flat=True))
        access_all_collections_orm = CollectionORM.objects.filter(team_id__in=access_all_teams_orm)

        limit_members_orm = members_orm.filter(role_id__in=[MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER])
        collection_members_orm = CollectionMemberORM.objects.filter(member__in=limit_members_orm)
        hide_password_collection_ids = list(
            collection_members_orm.filter(hide_passwords=True).values_list('collection_id', flat=True)
        )
        collection_members_ids = list(collection_members_orm.values_list('collection_id', flat=True))
        limit_collections_orm = CollectionORM.objects.filter(id__in=collection_members_ids)

        collections_orm = (access_all_collections_orm | limit_collections_orm).distinct()
        if filter_ids:
            collections_orm = collections_orm.filter(id__in=filter_ids)
        collections_orm = collections_orm.annotate(
            hide_passwords=Case(
                When(id__in=hide_password_collection_ids, then=True),
                default=False,
                output_field=BooleanField()
            )
        ).order_by('-creation_date').select_related('team')

        return [
            ModelParser.team_parser().parse_collection(collection_orm=collection_orm)
            for collection_orm in collections_orm
        ]

    # ------------------------ Get Collection resource --------------------- #
    def get_by_id(self, collection_id: str) -> Optional[Collection]:
        try:
            collection_orm = CollectionORM.objects.get(id=collection_id)
            return ModelParser.team_parser().parse_collection(collection_orm=collection_orm)
        except CollectionORM.DoesNotExist:
            return None

    # ------------------------ Create Collection resource --------------------- #

    # ------------------------ Update Collection resource --------------------- #

    # ------------------------ Delete Collection resource --------------------- #
