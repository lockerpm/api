from typing import Optional, List, Tuple, Dict, NoReturn

import jwt

from locker_server.core.entities.enterprise.enterprise import Enterprise
from locker_server.core.entities.enterprise.group.group_member import EnterpriseGroupMember
from locker_server.core.entities.enterprise.member.enterprise_member import EnterpriseMember
from locker_server.core.entities.user.user import User
from locker_server.core.exceptions.enterprise_member_exception import EnterpriseMemberDoesNotExistException, \
    EnterpriseMemberUpdatedFailedException, EnterpriseMemberInvitationUpdatedFailedException
from locker_server.core.repositories.enterprise_group_member_repository import EnterpriseGroupMemberRepository
from locker_server.core.repositories.enterprise_member_repository import EnterpriseMemberRepository
from locker_server.core.repositories.enterprise_repository import EnterpriseRepository
from locker_server.core.repositories.user_plan_repository import UserPlanRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.constants.enterprise_members import E_MEMBER_STATUS_INVITED, E_MEMBER_STATUS_REQUESTED, \
    E_MEMBER_STATUS_CONFIRMED
from locker_server.shared.constants.event import EVENT_E_MEMBER_UPDATED_ROLE
from locker_server.shared.constants.token import TOKEN_EXPIRED_TIME_INVITE_MEMBER, TOKEN_TYPE_INVITE_MEMBER, \
    TOKEN_PREFIX
from locker_server.shared.external_services.locker_background.constants import BG_EVENT
from locker_server.shared.utils.app import now


class EnterpriseMemberService:
    """
    This class represents Use Cases related Enterprise Member
    """

    def __init__(self, enterprise_repository: EnterpriseRepository,
                 enterprise_member_repository: EnterpriseMemberRepository,
                 enterprise_group_member_repository: EnterpriseGroupMemberRepository,
                 user_repository: UserRepository,
                 user_plan_repository: UserPlanRepository
                 ):
        self.enterprise_repository = enterprise_repository
        self.enterprise_member_repository = enterprise_member_repository
        self.enterprise_group_member_repository = enterprise_group_member_repository
        self.user_repository = user_repository
        self.user_plan_repository = user_plan_repository

    def list_enterprise_members(self, **filters) -> List[EnterpriseMember]:
        enterprise_members = self.enterprise_member_repository.list_enterprise_members(**filters)
        return enterprise_members

    def count_enterprise_members(self, **filters) -> int:
        enterprise_member_num = self.enterprise_member_repository.count_enterprise_members(**filters)
        return enterprise_member_num

    def list_group_member_by_enterprise_member_id(self, enterprise_member_id: str) -> List[EnterpriseGroupMember]:
        group_members = self.enterprise_group_member_repository.list_enterprise_group_member_by_member_id(
            enterprise_member_id=enterprise_member_id
        )
        return group_members

    def list_groups_name_by_enterprise_member_id(self, enterprise_member_id: str) -> List[str]:
        return self.enterprise_group_member_repository.list_groups_name_by_enterprise_member_id(enterprise_member_id)

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

    def list_enterprise_member_user_ids(self, **filter_params) -> List[int]:
        return self.enterprise_member_repository.list_enterprise_member_user_ids(**filter_params)

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
        user_ids_param = []
        for member in members_data:
            if member.get('user_id'):
                user_ids_param.append(member.get("user_id"))
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

    def create_multiple_members(self, members_data) -> int:
        return self.enterprise_member_repository.create_multiple_member(members_create_data=members_data)

    def invite_multiple_member(self,
                               secret: str, current_enterprise: Enterprise,
                               members_data: [Dict], scope: str = None
                               ) -> Tuple:
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

    def update_enterprise_member(self,
                                 current_user: User, enterprise_member: EnterpriseMember, role: str = None,
                                 status: str = None, **update_data
                                 ) -> Tuple:
        change_status = False
        change_role = False
        member_update_data = update_data.copy()
        if role:
            if enterprise_member.user and enterprise_member.user.user_id == current_user.user_id or enterprise_member.is_primary:
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

    def activated_member(self, enterprise_member: EnterpriseMember, activated: bool, current_user: User) \
            -> EnterpriseMember:
        if enterprise_member.status != E_MEMBER_STATUS_CONFIRMED:
            raise EnterpriseMemberDoesNotExistException
        if enterprise_member.user and enterprise_member.user.user_id == current_user.user_id:
            raise EnterpriseMemberUpdatedFailedException
        enterprise_member_update_data = {
            "is_activated": activated
        }
        updated_enterprise_member = self.enterprise_member_repository.update_enterprise_member(
            enterprise_member_id=enterprise_member.enterprise_member_id,
            enterprise_member_update_data=enterprise_member_update_data
        )
        if not updated_enterprise_member:
            raise EnterpriseMemberDoesNotExistException
        return updated_enterprise_member

    def delete_group_member_by_member_id(self, enterprise_member_id: str) -> NoReturn:
        self.enterprise_group_member_repository.delete_group_members_by_member_id(
            enterprise_member_id=enterprise_member_id
        )

    def unblock_enterprise_member(self, current_user: User, enterprise_member: EnterpriseMember) -> NoReturn:
        enterprise_member = self.enterprise_member_repository.get_enterprise_member_by_id(
            member_id=enterprise_member.enterprise_member_id
        )
        if not enterprise_member:
            raise EnterpriseMemberDoesNotExistException
        if enterprise_member.status != E_MEMBER_STATUS_CONFIRMED:
            raise EnterpriseMemberDoesNotExistException
        if enterprise_member.user and enterprise_member.user and enterprise_member.user.user_id == current_user.user_id:
            raise EnterpriseMemberUpdatedFailedException
        if enterprise_member.user:
            user_update_data = {
                "login_failed_attempts": 0,
                "login_block_until": None
            }
            self.user_repository.update_login_time_user(
                user_id=enterprise_member.user.user_id,
                update_data=user_update_data
            )

    def update_user_invitations(self, current_user: User, enterprise_member_id: str, status: str) -> EnterpriseMember:
        member_invitation = self.enterprise_member_repository.get_enterprise_member_by_id(
            member_id=enterprise_member_id
        )
        if not member_invitation or \
                (member_invitation.user and member_invitation.user.user_id != current_user.user_id) or \
                member_invitation.status != E_MEMBER_STATUS_INVITED:
            raise EnterpriseMemberDoesNotExistException
        # If the member has a domain => Not allow reject
        if member_invitation.domain:
            if status == "reject":
                raise EnterpriseMemberInvitationUpdatedFailedException
            if member_invitation.domain.auto_approve is True:
                updated_member_invitation = self.enterprise_member_repository.update_enterprise_member(
                    enterprise_member_id=member_invitation.enterprise_member_id,
                    enterprise_member_update_data={
                        "status": E_MEMBER_STATUS_CONFIRMED,
                        "access_time": now(),
                    }
                )
            else:
                updated_member_invitation = self.enterprise_member_repository.update_enterprise_member(
                    enterprise_member_id=member_invitation.enterprise_member_id,
                    enterprise_member_update_data={
                        "status": E_MEMBER_STATUS_REQUESTED,
                    }
                )
        else:
            if status == "confirmed":
                updated_member_invitation = self.enterprise_member_repository.update_enterprise_member(
                    enterprise_member_id=member_invitation.enterprise_member_id,
                    enterprise_member_update_data={
                        "status": E_MEMBER_STATUS_CONFIRMED,
                        "access_time": now(),
                    }
                )
            else:
                self.enterprise_member_repository.delete_enterprise_member(
                    enterprise_member_id=member_invitation.enterprise_member_id
                )
                updated_member_invitation = None
        return updated_member_invitation

    def confirm_invitation(self, email: str, user_id: str) -> List[str]:
        member_user, is_created = self.user_repository.retrieve_or_create_by_id(user_id=user_id)
        invitations = self.list_enterprise_members(**{
            "email": email,
            "status": E_MEMBER_STATUS_INVITED
        })
        enterprise_ids = [invitation.enterprise.enterprise_id for invitation in invitations]
        for invitation in invitations:
            enterprise = invitation.enterprise
            current_total_members = self.enterprise_member_repository.count_enterprise_members(**{
                "enterprise_id": enterprise.enterprise_id
            })
            primary_user = self.enterprise_member_repository.get_primary_member(
                enterprise_id=enterprise.enterprise_id
            ).user
            primary_plan = self.user_plan_repository.get_user_plan(user_id=primary_user.user_id)
            max_allow_members = primary_plan.get_max_allow_members()
            if max_allow_members and current_total_members + 1 > max_allow_members:
                continue
            self.enterprise_member_repository.update_enterprise_member(
                enterprise_member_id=invitation.enterprise_member_id,
                enterprise_member_update_data={
                    "email": None,
                    "user_id": member_user.user_id,
                    "token_invitation": None
                }
            )
        return enterprise_ids

    def delete_group_members_by_member_id(self, enterprise_member_id: str):
        self.enterprise_group_member_repository.delete_group_members_by_member_id(
            enterprise_member_id=enterprise_member_id
        )

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
