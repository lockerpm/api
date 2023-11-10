from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_group_model, get_group_member_model
from locker_server.api_orm.utils.revision_date import bump_account_revision_date
from locker_server.core.entities.team.collection import Collection
from locker_server.core.entities.team.group import Group
from locker_server.core.entities.team.group_member import GroupMember
from locker_server.core.entities.team.team import Team
from locker_server.core.repositories.team_group_repository import TeamGroupRepository


GroupORM = get_group_model()
GroupMemberORM = get_group_member_model()
ModelParser = get_model_parser()


class TeamGroupORMRepository(TeamGroupRepository):
    @staticmethod
    def _get_group_orm(group_id: str) -> Optional[GroupORM]:
        try:
            return GroupORM.objects.get(id=group_id)
        except GroupORM.DoesNotExist:
            return None

    # ------------------------ List TeamGroup resource ------------------- #
    def list_groups_by_sharing_id(self, sharing_id: str) -> List[Group]:
        groups_orm = GroupORM.objects.filter(team_id=sharing_id).order_by('-id').select_related('enterprise_group')
        return [ModelParser.team_parser().parse_group(group_orm=group_orm) for group_orm in groups_orm]

    def list_group_members(self, group_id: str, **filter_params) -> List[GroupMember]:
        group_members_orm = GroupMemberORM.objects.filter(
            group_id=group_id
        ).select_related('group').select_related('member')
        statuses_param = filter_params.get("statuses")
        user_ids_param = filter_params.get("user_ids")
        if statuses_param:
            group_members_orm = group_members_orm.filter(member__status__in=statuses_param)
        if user_ids_param:
            group_members_orm = group_members_orm.filter(member__user_id__in=user_ids_param)
        return [
            ModelParser.team_parser().parse_group_member(group_member_orm=group_member_orm)
            for group_member_orm in group_members_orm
        ]

    def list_group_members_user_ids(self, group_id: str) -> List[int]:
        return list(GroupMemberORM.objects.filter(
            group_id=group_id
        ).values_list('member__user_id', flat=True))

    # ------------------------ Get TeamGroup resource --------------------- #
    def get_share_group_by_id(self, sharing_id: str, group_id: str) -> Optional[Group]:
        try:
            group_orm = GroupORM.objects.get(id=group_id, team_id=sharing_id)
        except GroupORM.DoesNotExist:
            return None
        return ModelParser.team_parser().parse_group(group_orm=group_orm)

    def get_share_group_by_enterprise_group_id(self, sharing_id: str, enterprise_group_id: str) -> Optional[Group]:
        try:
            group_orm = GroupORM.objects.get(enterprise_group_id=enterprise_group_id, team_id=sharing_id)
        except GroupORM.DoesNotExist:
            return None
        return ModelParser.team_parser().parse_group(group_orm=group_orm)

    # ------------------------ Create TeamGroup resource --------------------- #

    # ------------------------ Update TeamGroup resource --------------------- #
    def update_group_role_invitation(self, group: Group, role_id: str) -> Optional[Group]:
        group_orm = self._get_group_orm(group_id=group.group_id)
        if not group_orm:
            return None
        group_orm.role_id = role_id
        group_orm.save()
        group_user_ids = list(group_orm.groups_members.values_list('member__user_id', flat=True))
        group_orm.team.team_members.filter(is_added_by_group=True, user_id__in=group_user_ids).update(role_id=role_id)
        # Bump revision date
        bump_account_revision_date(team=group_orm.team, **{"group_ids": [group_orm.enterprise_group_id]})
        return ModelParser.team_parser().parse_group(group_orm=group_orm)

    # ------------------------ Delete TeamGroup resource --------------------- #

