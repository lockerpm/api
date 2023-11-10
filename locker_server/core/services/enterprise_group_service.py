from typing import List, Optional

from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.enterprise.group.group import EnterpriseGroup
from locker_server.core.entities.enterprise.group.group_member import EnterpriseGroupMember
from locker_server.core.entities.user.user import User
from locker_server.core.exceptions.enterprise_group_exception import EnterpriseGroupDoesNotExistException
from locker_server.core.repositories.enterprise_group_member_repository import EnterpriseGroupMemberRepository
from locker_server.core.repositories.enterprise_group_repository import EnterpriseGroupRepository
from locker_server.core.repositories.enterprise_member_repository import EnterpriseMemberRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED
from locker_server.shared.utils.app import diff_list


class EnterpriseGroupService:
    """
    This class represents Use cases related EnterpriseGroupORM
    """

    def __init__(self,
                 enterprise_group_repository: EnterpriseGroupRepository,
                 enterprise_group_member_repository: EnterpriseGroupMemberRepository,
                 enterprise_member_repository: EnterpriseMemberRepository,
                 user_repository: UserRepository
                 ):
        self.enterprise_member_repository = enterprise_member_repository
        self.enterprise_group_repository = enterprise_group_repository
        self.enterprise_group_member_repository = enterprise_group_member_repository
        self.user_repository = user_repository

    def list_enterprise_groups(self, **filters) -> List[EnterpriseGroup]:
        return self.enterprise_group_repository.list_enterprise_groups(**filters)

    def get_group_by_id(self, enterprise_group_id) -> Optional[EnterpriseGroup]:
        group = self.enterprise_group_repository.get_by_id(
            enterprise_group_id=enterprise_group_id
        )
        if not group:
            raise EnterpriseGroupDoesNotExistException
        return group

    def create_group(self, enterprise: Enterprise, user: User, enterprise_group_create_data) -> EnterpriseGroup:
        enterprise_group_create_data.update({
            "enterprise_id": enterprise.enterprise_id,
            "created_by_id": user.user_id
        })
        new_group = self.enterprise_group_repository.create_enterprise_group(
            enterprise_group_create_data=enterprise_group_create_data
        )
        return new_group

    def update_group(self, group_id: str, group_update_data) -> Optional[EnterpriseGroup]:
        updated_enterprise_group = self.enterprise_group_repository.update_enterprise_group(
            enterprise_group_id=group_id,
            enterprise_group_update_data=group_update_data
        )
        if not updated_enterprise_group:
            raise EnterpriseGroupDoesNotExistException
        return updated_enterprise_group

    def delete_group_by_id(self, enterprise_group_id: str) -> bool:
        return self.enterprise_group_repository.delete_enterprise_group_by_id(
            enterprise_group_id=enterprise_group_id
        )

    def list_group_members(self, **filters) -> List[EnterpriseGroupMember]:
        return self.enterprise_group_member_repository.list_enterprise_group_members(**filters)

    def count_group_members(self, enterprise_group_id: str) -> int:
        return self.enterprise_group_member_repository.count_enterprise_group_members(enterprise_group_id)

    def update_members(self, enterprise_group: EnterpriseGroup, enterprise_member_ids: List[str]) -> List[str]:
        existed_enterprise_members = self.enterprise_member_repository.list_enterprise_members(**{
            "status": E_MEMBER_STATUS_CONFIRMED,
            "ids": enterprise_member_ids,
            "is_activated": "1"
        })
        existed_enterprise_member_ids = [member.enterprise_member_id for member in existed_enterprise_members]
        group_members = self.enterprise_group_member_repository.list_enterprise_group_members(**{
            "enterprise_group_id": enterprise_group.enterprise_group_id
        })
        existed_group_enterprise_member_ids = [
            group_member.member.enterprise_member_id for group_member in group_members
        ]
        deleted_member_ids = diff_list(existed_group_enterprise_member_ids, existed_enterprise_member_ids)
        new_member_ids = diff_list(existed_enterprise_member_ids, existed_group_enterprise_member_ids)

        # Remove group members
        deleted_user_ids = self.enterprise_group_member_repository.delete_multiple_by_member_ids(
            enterprise_group=enterprise_group,
            deleted_member_ids=deleted_member_ids
        )
        for deleted_user_id in deleted_user_ids:
            self.user_repository.delete_sync_cache_data(user_id=deleted_user_id)
        group_members_create_data = [{
            "member_id": member_id,
            "group_id": enterprise_group.enterprise_group_id
        } for member_id in new_member_ids]
        self.enterprise_group_member_repository.create_multiple_group_member(
            group_members_create_data=group_members_create_data
        )
        return new_member_ids
