from typing import Optional, List, Tuple, Dict, NoReturn

import jwt

from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.enterprise.member.enterprise_member import EnterpriseMember
from locker_server.core.entities.user.user import User
from locker_server.core.exceptions.enterprise_member_exception import EnterpriseMemberDoesNotExistException, \
    EnterpriseMemberUpdatedFailedException
from locker_server.core.repositories.enterprise_group_member_repository import EnterpriseGroupMemberRepository
from locker_server.core.repositories.enterprise_member_repository import EnterpriseMemberRepository
from locker_server.core.repositories.enterprise_repository import EnterpriseRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.constants.enterprise_members import E_MEMBER_STATUS_INVITED, E_MEMBER_STATUS_REQUESTED
from locker_server.shared.constants.event import EVENT_E_MEMBER_UPDATED_ROLE
from locker_server.shared.constants.token import TOKEN_EXPIRED_TIME_INVITE_MEMBER, TOKEN_TYPE_INVITE_MEMBER, \
    TOKEN_PREFIX
from locker_server.shared.external_services.locker_background.constants import BG_EVENT
from locker_server.shared.utils.app import now


class EnterpriseGroupMemberService:
    """
    This class represents Use Cases related Enterprise Group Member
    """

    def __init__(self, enterprise_repository: EnterpriseRepository,
                 enterprise_member_repository: EnterpriseMemberRepository,
                 enterprise_group_member_repository: EnterpriseGroupMemberRepository,
                 user_repository: UserRepository
                 ):
        self.enterprise_repository = enterprise_repository
        self.enterprise_member_repository = enterprise_member_repository
        self.enterprise_group_member_repository = enterprise_group_member_repository
        self.user_repository = user_repository

    def list_enterprise_members(self, **filters) -> List[EnterpriseMember]:
        enterprise_members = self.enterprise_member_repository.list_enterprise_members(**filters)
        for enterprise_member in enterprise_members:
            group_members = self.enterprise_group_member_repository.list_enterprise_group_member_by_member_id(
                enterprise_member_id=enterprise_member.enterprise_member_id
            )
            enterprise_member.group_members = group_members
        return enterprise_members

    def list_enterprise_member_user_id_by_roles(self, enterprise_id: str, role_ids: List[str]) -> List[str]:
        return self.enterprise_member_repository.list_enterprise_member_user_id_by_roles(
            enterprise_id=enterprise_id,
            role_ids=role_ids
        )

    def list_enterprise_member_user_id_by_members(self, enterprise_id: str, member_ids: List[str]) -> List[str]:
        return self.enterprise_member_repository.list_enterprise_member_user_id_by_members(
            enterprise_id=enterprise_id,
            member_ids=member_ids
        )

    def get_member_by_id(self, member_id: str) -> Optional[EnterpriseMember]:
        member = self.enterprise_member_repository.get_enterprise_member_by_id(
            member_id=member_id
        )
        if not member:
            raise EnterpriseMemberDoesNotExistException
        return member

    def get_member_by_user(self, user_id: int, enterprise_id: str) -> Optional[EnterpriseMember]:
        enterprise_member = self.enterprise_member_repository.get_enterprise_member_by_user_id(
            user_id=user_id,
            enterprise_id=enterprise_id
        )
        if not enterprise_member:
            raise EnterpriseMemberDoesNotExistException
        return enterprise_member

    def list_enterprise_member_user_id_by_group_id(self, enterprise_id: str, group_id: str) -> List[str]:
        return self.enterprise_group_member_repository.list_enterprise_group_member_user_id_by_id(
            enterprise_id=enterprise_id,
            enterprise_group_id=group_id
        )

    def create_multiple_member(self, current_enterprise: Enterprise, members_data: list) -> Tuple:
        added_members = []
        non_added_members = []
        members_create_data = []
        user_ids_param = [member.get("user_id") for member in members_data]
        existed_enterprise_members = self.enterprise_member_repository.list_enterprise_members(**{
            "user_ids": user_ids_param

        })
        existed_enterprise_member_dict = {}
        for enterprise_member in existed_enterprise_members:
            user_id = enterprise_member.user.user_id
            enterprise_id = enterprise_member.enterprise.enterprise_id
            user_dict = existed_enterprise_member_dict.get(user_id)
            if not user_dict:
                existed_enterprise_member_dict[user_id] = {
                    enterprise_id: enterprise_member
                }
            else:
                existed_enterprise_member_dict[user_id].update({
                    enterprise_id: enterprise_member
                })
        for member in members_data:
            user_id = member.get("user_id")
            if not user_id:
                non_added_members.append(user_id)
                continue
            existed_user_members = existed_enterprise_member_dict.get(user_id)
            if existed_user_members:
                non_added_members.append(user_id)
                continue

            # Already added
            if user_id in added_members:
                non_added_members.append(user_id)
                continue
            # create new member
            user, is_created = self.user_repository.retrieve_or_create_by_id(user_id=user_id)
            member_create_data = {
                "role": member["role"],
                "enterprise_id": current_enterprise.enterprise_id,
                "user_id": user.user_id,
                "status": E_MEMBER_STATUS_INVITED
            }
            members_create_data.append(member_create_data)
            added_members.append(user.user_id)
        self.enterprise_member_repository.create_multiple_member(members_create_data=members_create_data)
        return added_members, list(set(non_added_members))

    def invite_multiple_member(self, secret: str, current_enterprise: Enterprise, members_data: [Dict],
                               scope: str = None) -> Tuple:
        emails_param = [member.get("email") for member in members_data]
        existed_members = self.enterprise_member_repository.list_enterprise_members_by_emails(
            emails_param=emails_param
        )
        existed_email_members = [member.email for member in existed_members]
        added_members = []
        non_added_members = []
        added_emails = []
        for member_data in members_data:
            member_email = member_data.get("email")
            if member_email in existed_email_members:
                non_added_members.append(member_email)
                continue
            if member_email in added_emails:
                non_added_members.append(member_email)
                continue
            token_value = self.create_invitation_token(
                secret=secret,
                email=member_email,
                enterprise_id=current_enterprise.enterprise_id,
                scope=scope
            )
            member_create_data = {
                "enterprise_id": current_enterprise.enterprise_id,
                "role_id": member_data.get("role"),
                "email": member_email,
                "status": E_MEMBER_STATUS_INVITED,
                "token_invitation": token_value
            }
            new_member = self.enterprise_member_repository.create_member(
                member_create_data=member_create_data
            )
            added_members.append({
                "enterprise_id": current_enterprise.enterprise_id,
                "enterprise_name": current_enterprise.name,
                "token": new_member.token_invitation,
                "email": member_email
            })
            added_emails.append(member_email)
        return added_members, non_added_members

    def update_enterprise_member(self, current_user: User, enterprise_member: EnterpriseMember, role: str = None,
                                 status: str = None, **update_data) -> Tuple:
        change_status = False
        change_role = False
        member_update_data = update_data.copy()
        if role:
            if enterprise_member.user.user_id == current_user.user_id or enterprise_member.is_primary:
                raise EnterpriseMemberUpdatedFailedException
            member_update_data.update({
                "role": role
            })
        if status:
            if enterprise_member.status == E_MEMBER_STATUS_REQUESTED:
                member_update_data.update({
                    "status": status
                })
                change_status = True
        updated_enterprise_member = self.enterprise_member_repository.update_enterprise_member(
            enterprise_member_id=enterprise_member.enterprise_member_id,
            enterprise_member_update_data=member_update_data
        )
        if not updated_enterprise_member:
            raise EnterpriseMemberDoesNotExistException
        return change_status, change_role, updated_enterprise_member

    def delete_enterprise_member(self, enterprise_member_id: str) -> NoReturn:
        deleted_enterprise_member = self.enterprise_member_repository.delete_enterprise_member(
            enterprise_member_id=enterprise_member_id
        )
        if not deleted_enterprise_member:
            raise EnterpriseMemberDoesNotExistException

    @staticmethod
    def create_invitation_token(secret: str, email: str, enterprise_id: str, scope: str = None) -> str:
        created_time = now()
        expired_time = created_time + TOKEN_EXPIRED_TIME_INVITE_MEMBER * 3600
        payload = {
            "scope": scope,
            "member": email,
            "enterprise": enterprise_id,
            "created_time": created_time,
            "expired_time": expired_time,
            "token_type": TOKEN_TYPE_INVITE_MEMBER
        }
        token_value = jwt.encode(payload, secret, algorithm="HS256")
        token_value = TOKEN_PREFIX + token_value
        return token_value
