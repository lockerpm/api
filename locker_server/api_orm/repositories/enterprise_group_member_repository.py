from typing import Union, Dict, Optional, List, NoReturn
from abc import ABC, abstractmethod

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_enterprise_group_member_model, get_group_model, \
    get_team_member_model
from locker_server.core.entities.enterprise.group.group import EnterpriseGroup
from locker_server.core.entities.enterprise.group.group_member import EnterpriseGroupMember
from locker_server.core.repositories.enterprise_group_member_repository import EnterpriseGroupMemberRepository
from locker_server.shared.constants.members import MEMBER_ROLE_OWNER

EnterpriseGroupMemberORM = get_enterprise_group_member_model()
ModelParser = get_model_parser()
GroupORM = get_group_model()
TeamMemberORM = get_team_member_model()


class EnterpriseGroupMemberORMRepository(EnterpriseGroupMemberRepository):
    # ------------------------ List EnterpriseGroupMember resource ------------------- #
    def list_by_group_id(self, enterprise_group_id: str) -> List[EnterpriseGroupMember]:
        group_members_orm = EnterpriseGroupMemberORM.objects.filter(
            group_id=enterprise_group_id
        ).select_related('group').select_related('member')
        return [ModelParser.enterprise_parser().parse_enterprise_group_member(
            enterprise_group_member_orm=group_member_orm
        ) for group_member_orm in group_members_orm]

    def list_group_member_user_email(self, enterprise_group_id: str) -> List:
        members = EnterpriseGroupMemberORM.objects.filter(
            group_id=enterprise_group_id
        ).values('member__user_id', 'member__email')
        return [{"user_id": m.get("member__user_id"), "email": m.get("member__email")} for m in members]

    def list_enterprise_group_member_user_id_by_id(self, enterprise_id: str, enterprise_group_id: str) -> List[str]:
        user_ids = EnterpriseGroupMemberORM.objects.filter(
            group_id=enterprise_group_id,
            group__enterprise_id=enterprise_id
        ).values_list("member__user_id", flat=True)
        return list(user_ids)

    def list_enterprise_group_member_by_member_id(self, enterprise_member_id: str) -> List[EnterpriseGroupMember]:
        group_members_orm = EnterpriseGroupMemberORM.objects.filter(
            member_id=enterprise_member_id
        ).select_related('member').select_related('group')
        return [
            ModelParser.enterprise_parser().parse_enterprise_group_member(
                enterprise_group_member_orm=group_member_orm
            ) for group_member_orm in group_members_orm
        ]

    def list_groups_name_by_enterprise_member_id(self, enterprise_member_id: str) -> List[str]:
        return list(
            EnterpriseGroupMemberORM.objects.filter(
                member_id=enterprise_member_id
            ).values_list('group__name', flat=True)
        )

    def list_enterprise_group_members(self, **filters) -> List[EnterpriseGroupMember]:
        enterprise_group_id_param = filters.get("enterprise_group_id")
        if enterprise_group_id_param:
            enterprise_group_members_orm = EnterpriseGroupMemberORM.objects.filter(
                group_id=enterprise_group_id_param
            ).select_related("member").select_related("group").order_by("member_id")
        else:
            enterprise_group_members_orm = EnterpriseGroupMemberORM.objects.all().select_related(
                "group"
            ).select_related("member").select_related("group").order_by("member_id")
        return [
            ModelParser.enterprise_parser().parse_enterprise_group_member(
                enterprise_group_member_orm=enterprise_group_member_orm
            )
            for enterprise_group_member_orm in enterprise_group_members_orm
        ]

    def count_enterprise_group_members(self, enterprise_group_id) -> int:
        return EnterpriseGroupMemberORM.objects.filter(group_id=enterprise_group_id).count()

    # ------------------------ Get EnterpriseGroupMember resource --------------------- #

    # ------------------------ Create EnterpriseGroupMember resource --------------------- #
    def create_multiple_group_member(self, group_members_create_data: [Dict]) -> NoReturn:
        EnterpriseGroupMemberORM.create_multiple(group_members_create_data)
    # ------------------------ Update EnterpriseGroupMember resource --------------------- #

    # ------------------------ Delete EnterpriseGroupMember resource --------------------- #
    def delete_group_members_by_member_id(self, enterprise_member_id: str) -> bool:
        group_members_orm = EnterpriseGroupMemberORM.objects.filter(
            member_id=enterprise_member_id
        )
        group_members_orm.delete()
        return True

    def delete_multiple_by_member_ids(self, enterprise_group: EnterpriseGroup, deleted_member_ids: [str]) -> List[int]:
        deleted_groups_members = EnterpriseGroupMemberORM.objects.filter(
            member_id__in=deleted_member_ids,
            group_id=enterprise_group.enterprise_group_id
        )
        deleted_user_ids = list(deleted_groups_members.values_list('member__user_id', flat=True))
        sharing_group_members = GroupORM.objects.filter(
            groups_members__member__user_id__in=deleted_user_ids
        ).values_list('groups_members__member_id', flat=True)
        TeamMemberORM.objects.filter(
            id__in=list(sharing_group_members), is_added_by_group=True
        ).exclude(role_id=MEMBER_ROLE_OWNER).delete()
        deleted_groups_members.delete()
        return deleted_user_ids
