from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_team_model, get_collection_model, get_team_member_model
from locker_server.core.entities.team.collection import Collection
from locker_server.core.entities.team.team import Team
from locker_server.core.repositories.team_repository import TeamRepository
from locker_server.shared.constants.members import MEMBER_ROLE_OWNER

TeamORM = get_team_model()
TeamMemberORM = get_team_member_model()
CollectionORM = get_collection_model()
ModelParser = get_model_parser()


class TeamORMRepository(TeamRepository):
    @staticmethod
    def _get_team_orm(team_id: str) -> Optional[TeamORM]:
        try:
            team_orm = TeamORM.objects.get(id=team_id)
            return team_orm
        except TeamORM.DoesNotExist:
            return None

    # ------------------------ List Team resource ------------------- #
    def list_team_collection_ids(self, team_id: str) -> List[str]:
        return list(CollectionORM.objects.filter(team_id=team_id).values_list('id', flat=True))

    def list_owner_sharing_ids(self, user_id: int) -> List[str]:
        try:
            default_team_orm = TeamMemberORM.objects.get(user_id=user_id, is_default=True).team
        except TeamMemberORM.DoesNotExist:
            default_team_orm = None
        default_team_id = default_team_orm.id if default_team_orm else None
        owner_teams = TeamMemberORM.objects.filter(
            user_id=user_id,
            role__name=MEMBER_ROLE_OWNER,
            is_primary=True,
            team__key__isnull=False,
            team__personal_share=True
        ).exclude(team_id=default_team_id)
        return list(owner_teams.values_list('team_id', flat=True))

    # ------------------------ Get Team resource --------------------- #
    def get_by_id(self, team_id: str) -> Optional[Team]:
        team_orm = self._get_team_orm(team_id=team_id)
        return ModelParser.team_parser().parse_team(team_orm=team_orm) if team_orm else None

    def get_default_collection(self, team_id: str) -> Optional[Collection]:
        try:
            collection_orm = CollectionORM.objects.get(team_id=team_id, is_default=True)
        except CollectionORM.DoesNotExist:
            return None
        return ModelParser.team_parser().parse_collection(collection_orm=collection_orm)

    def get_team_collection_by_id(self, team_id: str, collection_id: str) -> Optional[Collection]:
        try:
            collection_orm = CollectionORM.objects.get(team_id=team_id, id=collection_id)
        except CollectionORM.DoesNotExist:
            return None
        return ModelParser.team_parser().parse_collection(collection_orm=collection_orm)

    # ------------------------ Create PMPlan resource --------------------- #

    # ------------------------ Update PMPlan resource --------------------- #

    # ------------------------ Delete PMPlan resource --------------------- #
    def delete_multiple_teams(self, team_ids: List[str]):
        TeamORM.objects.filter(id__in=team_ids).delete()

    def delete_sharing_with_me(self, user_id: int):
        members_orm = TeamMemberORM.objects.filter(
            user_id=user_id, team__key__isnull=False, team__personal_share=True
        ).exclude(role__name=MEMBER_ROLE_OWNER)
        shared_team_ids = members_orm.values_list('team_id', flat=True)
        owners = TeamMemberORM.objects.filter(
            team__key__isnull=False, role_id=MEMBER_ROLE_OWNER, team_id__in=shared_team_ids
        ).values_list('user_id', flat=True)
        members_orm.delete()
        return owners
