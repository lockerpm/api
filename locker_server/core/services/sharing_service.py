import json
from typing import List, Optional, Dict, Union

from locker_server.core.entities.cipher.cipher import Cipher
from locker_server.core.entities.cipher.folder import Folder
from locker_server.core.entities.enterprise.group.group import EnterpriseGroup
from locker_server.core.entities.member.team_member import TeamMember
from locker_server.core.entities.team.collection import Collection
from locker_server.core.entities.team.group import Group
from locker_server.core.entities.team.team import Team
from locker_server.core.entities.user.user import User
from locker_server.core.exceptions.cipher_exception import *
from locker_server.core.exceptions.collection_exception import *
from locker_server.core.exceptions.enterprise_group_exception import EnterpriseGroupDoesNotExistException
from locker_server.core.exceptions.team_exception import TeamDoesNotExistException, TeamGroupDoesNotExistException
from locker_server.core.exceptions.team_member_exception import TeamMemberDoesNotExistException, \
    OwnerDoesNotExistException, TeamMemberEmailDoesNotExistException
from locker_server.core.repositories.cipher_repository import CipherRepository
from locker_server.core.repositories.device_repository import DeviceRepository
from locker_server.core.repositories.enterprise_group_member_repository import EnterpriseGroupMemberRepository
from locker_server.core.repositories.enterprise_group_repository import EnterpriseGroupRepository
from locker_server.core.repositories.enterprise_repository import EnterpriseRepository
from locker_server.core.repositories.folder_repository import FolderRepository
from locker_server.core.repositories.notification_setting_repository import NotificationSettingRepository
from locker_server.core.repositories.sharing_repository import SharingRepository
from locker_server.core.repositories.team_group_repository import TeamGroupRepository
from locker_server.core.repositories.team_member_repository import TeamMemberRepository
from locker_server.core.repositories.team_repository import TeamRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.constants.ciphers import MAP_CIPHER_TYPE_STR
from locker_server.shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED
from locker_server.shared.constants.event import EVENT_ITEM_SHARE_CREATED
from locker_server.shared.constants.members import *
from locker_server.shared.constants.user_notification import NOTIFY_SHARING
from locker_server.shared.external_services.fcm.constants import FCM_TYPE_CONFIRM_SHARE, FCM_TYPE_ACCEPT_SHARE, \
    FCM_TYPE_REJECT_SHARE, FCM_TYPE_NEW_SHARE, FCM_TYPE_NEW_SHARE_AFTER_OWNER_CONFIRMED
from locker_server.shared.external_services.fcm.fcm_request_entity import FCMRequestEntity
from locker_server.shared.external_services.fcm.fcm_sender import FCMSenderService
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_EVENT
from locker_server.shared.external_services.pm_sync import PwdSync, SYNC_EVENT_MEMBER_ACCEPTED, \
    SYNC_EVENT_CIPHER_UPDATE, SYNC_EVENT_COLLECTION_UPDATE, SYNC_EVENT_MEMBER_REJECT, SYNC_EVENT_MEMBER_INVITATION, \
    SYNC_EVENT_CIPHER, SYNC_EVENT_MEMBER_CONFIRMED, SYNC_EVENT_MEMBER_UPDATE, SYNC_EVENT_MEMBER_REMOVE, \
    SYNC_EVENT_CIPHER_SHARE, SYNC_EVENT_CIPHER_INVITATION
from locker_server.shared.utils.app import now
from locker_server.shared.utils.avatar import get_avatar


class SharingService:
    """
    This class represents Use Cases related Sharing
    """
    def __init__(self, sharing_repository: SharingRepository,
                 team_repository: TeamRepository,
                 team_member_repository: TeamMemberRepository,
                 team_group_repository: TeamGroupRepository,
                 user_repository: UserRepository,
                 notification_setting_repository: NotificationSettingRepository,
                 device_repository: DeviceRepository,
                 enterprise_group_repository: EnterpriseGroupRepository,
                 enterprise_group_member_repository: EnterpriseGroupMemberRepository,
                 cipher_repository: CipherRepository,
                 folder_repository: FolderRepository,
                 enterprise_repository: EnterpriseRepository):
        self.sharing_repository = sharing_repository
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.team_group_repository = team_group_repository
        self.user_repository = user_repository
        self.notification_setting_repository = notification_setting_repository
        self.device_repository = device_repository
        self.enterprise_group_repository = enterprise_group_repository
        self.enterprise_group_member_repository = enterprise_group_member_repository
        self.cipher_repository = cipher_repository
        self.folder_repository = folder_repository
        self.enterprise_repository = enterprise_repository

    @staticmethod
    def get_personal_share_type(member: TeamMember = None, role: str = None):
        if not role:
            role = member.role.name
        if role in [MEMBER_ROLE_MEMBER]:
            if member and member.hide_passwords is True:
                return MEMBER_SHARE_TYPE_ONLY_FILL
            else:
                return MEMBER_SHARE_TYPE_VIEW
        return MEMBER_SHARE_TYPE_EDIT

    def get_shared_members(self, personal_shared_team: Team,
                           exclude_owner=True, is_added_by_group=None) -> List[TeamMember]:
        return self.sharing_repository.get_shared_members(
            personal_shared_team=personal_shared_team, exclude_owner=exclude_owner, is_added_by_group=is_added_by_group
        )

    def get_shared_member(self, sharing_member_id: str) -> Optional[TeamMember]:
        team_member = self.team_member_repository.get_team_member_by_id(team_member_id=sharing_member_id)
        if not team_member:
            raise TeamMemberDoesNotExistException
        return team_member

    def get_by_id(self, sharing_id: str) -> Optional[Team]:
        sharing = self.team_repository.get_by_id(team_id=sharing_id)
        if not sharing:
            raise TeamDoesNotExistException
        return sharing

    def list_sharing_invitations(self, user_id: int, personal_share=True) -> List[TeamMember]:
        return self.sharing_repository.list_sharing_invitations(user_id=user_id, personal_share=personal_share)

    def update_sharing_invitation(self, sharing_invitation: TeamMember, status: str, user_fullname=None) -> TeamMember:
        user = sharing_invitation.user
        if not user_fullname:
            user_fullname = user.full_name
        sharing_id = sharing_invitation.team.team_id
        primary_owner = self.team_member_repository.get_primary_member(team_id=sharing_invitation.team.team_id)
        shared_type_name = None
        item_id = None
        cipher_id = None
        folder_id = None

        if status == "accept":
            member = self.sharing_repository.accept_invitation(member=sharing_invitation)
            member_status = member.status
            PwdSync(event=SYNC_EVENT_MEMBER_ACCEPTED, user_ids=[primary_owner.user.user_id, user.user_id]).send()
            # If share a cipher:
            if self.is_folder_sharing(sharing_id=sharing_id) is False:
                share_cipher = self.sharing_repository.get_share_cipher(sharing_id=sharing_id)
                if share_cipher:
                    shared_type_name = share_cipher.cipher_type
                    item_id = share_cipher.cipher_id
                    cipher_id = item_id
                    self.user_repository.delete_sync_cache_data(user_id=user.user_id)
                    PwdSync(event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[user.user_id]).send(
                        data={"id": share_cipher.cipher_id}
                    )
            # Else, share a folder
            else:
                share_collection = self.sharing_repository.get_share_collection(sharing_id=sharing_id)
                if share_collection:
                    shared_type_name = "folder"
                    item_id = share_collection.collection_id
                    folder_id = item_id
                    self.user_repository.delete_sync_cache_data(user_id=user.user_id)
                    PwdSync(event=SYNC_EVENT_COLLECTION_UPDATE, user_ids=[user.user_id]).send(
                        data={"id": share_collection.collection_id}
                    )

        # Reject this invitation
        else:
            if self.is_folder_sharing(sharing_id=sharing_id) is False:
                share_cipher = self.sharing_repository.get_share_cipher(sharing_id=sharing_id)
                shared_type_name = share_cipher.cipher_type if share_cipher else shared_type_name
                item_id = share_cipher.cipher_id if share_cipher else item_id
                cipher_id = item_id
            else:
                shared_type_name = "folder"
                share_collection = self.sharing_repository.get_share_collection(sharing_id=sharing_id)
                item_id = share_collection.collection_id if share_collection else item_id
                folder_id = item_id
            self.sharing_repository.reject_invitation(member=sharing_invitation)
            member_status = None
            PwdSync(event=SYNC_EVENT_MEMBER_REJECT, user_ids=[primary_owner.user.user_id, user.user_id]).send()

        # Push mobile notification
        mail_user_ids = self.notification_setting_repository.get_user_mail(
            category_id=NOTIFY_SHARING, user_ids=[primary_owner.user.user_id]
        )
        notification_user_ids = self.notification_setting_repository.get_user_notification(
            category_id=NOTIFY_SHARING, user_ids=[primary_owner.user.user_id]
        )
        if member_status == PM_MEMBER_STATUS_ACCEPTED:
            fcm_event = FCM_TYPE_CONFIRM_SHARE
        elif member_status == PM_MEMBER_STATUS_CONFIRMED:
            fcm_event = FCM_TYPE_ACCEPT_SHARE
        else:
            fcm_event = FCM_TYPE_REJECT_SHARE

        fcm_ids = self.device_repository.get_fcm_ids_by_user_ids(user_ids=notification_user_ids)
        fcm_message = FCMRequestEntity(
            fcm_ids=list(fcm_ids), priority="high",
            data={
                "event": fcm_event,
                "data": {
                    "id": sharing_id,
                    "share_type": shared_type_name,
                    "pwd_user_ids": [primary_owner.user.user_id],
                    "name": user_fullname,
                    "recipient_name": user_fullname,
                }
            }
        )
        FCMSenderService(is_background=True).run("send_message", **{"fcm_message": fcm_message})
        return {
            "status": status,
            "owner": primary_owner.user.user_id,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids,
            "member_status": member_status,
            "share_type": shared_type_name,
            "item_id": item_id,
            "folder_id": folder_id,
            "cipher_id": cipher_id
        }

    def get_sharing_owner(self, sharing_id: str) -> Optional[TeamMember]:
        owner = self.team_member_repository.get_primary_member(team_id=sharing_id)
        if not owner:
            raise OwnerDoesNotExistException
        return owner

    def is_folder_sharing(self, sharing_id: str) -> bool:
        return True if self.team_repository.list_team_collection_ids(team_id=sharing_id) else False

    def get_sharing_cipher_type(self, sharing_id: str) -> Union[str, int]:
        return self.sharing_repository.get_sharing_cipher_type(sharing_id=sharing_id)

    def _validate_share_groups(self, user: User, groups: List[Dict]) -> List[Dict]:
        if not groups:
            return groups
        user_enterprise_groups_ids = self.enterprise_group_repository.list_active_user_enterprise_group_ids(
            user_id=user.user_id
        )
        for group in groups:
            group_id = group.get("id")
            enterprise_group = self.enterprise_group_repository.get_by_id(enterprise_group_id=group_id)
            if not enterprise_group:
                raise EnterpriseGroupDoesNotExistException
            if group_id not in user_enterprise_groups_ids:
                raise EnterpriseGroupDoesNotExistException
            group_members = self.enterprise_group_member_repository.list_group_member_user_email(
                enterprise_group_id=group_id
            )
            members_user_ids = [member.get("user_id") for member in group_members if member.get("user_id")]
            members_emails = [member.get("email") for member in group_members if member.get("email")]
            members = group.get("members")
            user_ids = [member.get("user_id") for member in members if member.get("user_id")]
            emails = [member.get("email") for member in members if member.get("email") and not member.get("user_id")]
            if any(user_id not in members_user_ids for user_id in user_ids):
                raise TeamMemberDoesNotExistException
            if any(email not in members_emails for email in emails):
                raise TeamMemberEmailDoesNotExistException
        return groups

    def _validate_cipher(self, user: User, cipher: Dict) -> Optional[Cipher]:
        if not cipher:
            return None
        cipher_obj = self.cipher_repository.get_by_id(cipher_id=cipher.get("id"))
        if not cipher:
            raise CipherDoesNotExistException
        # If the cipher isn't shared?
        if cipher_obj.user and cipher_obj.user.user_id != user.user_id:
            raise CipherDoesNotExistException
        # If the cipher obj belongs to a team
        if cipher_obj.team:
            # Check the team is a personal sharing team?
            if cipher_obj.team.personal_share is False:
                raise CipherDoesNotExistException
            # Check the user is an owner?
            owner = self.team_member_repository.get_user_team_member(
                user_id=user.user_id, team_id=cipher_obj.team.team_id
            )
            if not owner or owner.role.name != MEMBER_ROLE_OWNER:
                raise CipherDoesNotExistException
            # Check the team only shares this cipher?
            if self.is_folder_sharing(sharing_id=cipher_obj.team.team_id) is True:
                raise CipherBelongCollectionException
        return cipher_obj

    def _validate_folder(self, user: User, folder: Dict) -> Optional[Folder]:
        if not folder:
            return None
        folder_id = folder.get("id")
        folder_name = folder.get("name")
        folder_ciphers = folder.get("ciphers") or []
        folder_obj = self.folder_repository.get_by_id(folder_id=folder_id)
        if not folder_obj or folder_obj.user.user_id != user.user_id:
            raise FolderDoesNotExistException
        # Check the list folder_ciphers in the folder
        folder_ciphers_obj = self.cipher_repository.list_cipher_ids_by_folder_id(
            user_id=user.user_id, folder_id=folder_id
        )
        for folder_cipher in folder_ciphers:
            if folder_cipher.get("id") not in list(folder_ciphers_obj):
                raise CipherBelongTeamException
        return folder_obj

    def _validate_stop_cipher(self, sharing_id: str, cipher: Dict) -> Optional[Cipher]:
        if not cipher:
            return None
        cipher_id = cipher.get("id")
        cipher_obj = self.cipher_repository.get_by_id(cipher_id=cipher_id)
        if not cipher_obj or cipher_obj.team.team_id != sharing_id:
            raise CipherDoesNotExistException
        return cipher_obj

    def _validate_stop_folder(self, sharing_id: str, folder: Dict) -> Optional[Collection]:
        if not folder:
            return None
        folder_id = folder.get("id")
        folder_name = folder.get("name")
        folder_ciphers = folder.get("ciphers") or []
        # Get collection of the team
        collection_obj = self.team_repository.get_team_collection_by_id(team_id=sharing_id, collection_id=folder_id)
        if not collection_obj:
            raise CollectionDoesNotExistException
        # Check the list folder_ciphers in the folder
        collection_ciphers_ids = self.cipher_repository.list_cipher_ids_by_collection_id(
            collection_id=collection_obj.collection_id
        )
        if collection_ciphers_ids and not folder_ciphers:
            raise StopCipherEmptyException

        for folder_cipher in folder_ciphers:
            if folder_cipher.get("id") not in collection_ciphers_ids:
                raise CipherBelongCollectionException

        return collection_obj

    def share_cipher_or_folder(self, user: User, sharing_key: str, members: List, groups: List,
                               cipher: Dict, shared_cipher_data: Dict, folder: Dict,
                               owner_name: str = None, ip: str = None) -> Dict:
        # First, validate members and groups
        groups = self._validate_share_groups(user=user, groups=groups)

        # Validate the cipher
        new_sharing, existed_member_users, non_existed_member_users = self._share_cipher_or_folder(
            user=user, sharing_key=sharing_key, members=members, groups=groups,
            cipher=cipher, shared_cipher_data=shared_cipher_data, folder=folder
        )

        # Sending sync event
        for u_id in existed_member_users + [user.user_id]:
            self.user_repository.delete_sync_cache_data(user_id=u_id)
        PwdSync(event=SYNC_EVENT_MEMBER_INVITATION, user_ids=existed_member_users + [user.user_id]).send()
        PwdSync(event=SYNC_EVENT_CIPHER_INVITATION, user_ids=existed_member_users).send()
        shared_type_name = None
        cipher_id = None
        folder_id = None
        if cipher:
            cipher_obj = self.sharing_repository.get_share_cipher(sharing_id=new_sharing.team_id)
            if cipher_obj:
                shared_type_name = cipher_obj.cipher_type
                cipher_id = cipher_obj.cipher_id
                self.user_repository.delete_sync_cache_data(user_id=user.user_id)
                PwdSync(
                    event=SYNC_EVENT_CIPHER_SHARE, user_ids=[user.user_id]
                ).send(data={"ids": [cipher_obj.cipher_id], "id": cipher_obj.cipher_id})

        if folder:
            shared_type_name = "folder"
            share_collection = self.sharing_repository.get_share_collection(sharing_id=new_sharing.team_id)
            folder_id = share_collection.collection_id if share_collection else None
            self.user_repository.delete_sync_cache_data(user_id=user.user_id)
            PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[user.user_id], team=new_sharing, add_all=True).send()

        # Sending mobile notification
        mail_user_ids = self.notification_setting_repository.get_user_mail(
            category_id=NOTIFY_SHARING, user_ids=existed_member_users
        )
        notification_user_ids = self.notification_setting_repository.get_user_notification(
            category_id=NOTIFY_SHARING, user_ids=existed_member_users
        )
        # Push mobile notification
        fcm_ids = self.device_repository.get_fcm_ids_by_user_ids(user_ids=notification_user_ids)
        try:
            owner_name = user.full_name
        except AttributeError:
            pass
        fcm_message = FCMRequestEntity(
            fcm_ids=fcm_ids, priority="high",
            data={
                "event": FCM_TYPE_NEW_SHARE,
                "data": {
                    "pwd_user_ids": notification_user_ids,
                    "share_type": shared_type_name,
                    "owner_name": owner_name
                }
            }
        )
        FCMSenderService(is_background=True).run("send_message", **{"fcm_message": fcm_message})

        # Update activity logs:
        user_enterprise_ids = self.enterprise_repository.list_user_enterprise_ids(user_id=user.user_id, **{
            "status": E_MEMBER_STATUS_CONFIRMED
        })
        if user_enterprise_ids:
            emails = [m.get("email") for m in members]
            item_type = MAP_CIPHER_TYPE_STR.get(shared_type_name) if shared_type_name != 'folder' else shared_type_name
            BackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
                "enterprise_ids": user_enterprise_ids,
                "user_id": user.user_id,
                "acting_user_id": user.user_id,
                "type": EVENT_ITEM_SHARE_CREATED,
                "ip_address": ip,
                "cipher_id": cipher_id,
                "collection_id": folder_id,
                "metadata": {"item_type": item_type, "emails": emails}
            })

        return {
            "new_sharing": new_sharing,
            "shared_type_name": shared_type_name,
            "folder_id": folder_id,
            "cipher_id": cipher_id,
            # "cipher_obj": cipher_obj,
            # "folder_obj": folder_obj,
            "existed_member_users": existed_member_users,
            "non_existed_member_users": non_existed_member_users,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids,
        }

    def _share_cipher_or_folder(self, user: User, sharing_key: str, members: List, groups: List,
                                cipher: Dict, shared_cipher_data: Dict, folder: Dict) -> Dict:
        cipher_obj = None
        folder_obj = None
        folder_name = None
        folder_ciphers = None

        # Validate the cipher
        if cipher:
            cipher_obj = self._validate_cipher(user=user, cipher=cipher)
            shared_cipher_data = json.loads(json.dumps(shared_cipher_data))

        if folder:
            folder_name = folder.get("name")
            folder_ciphers = folder.get("ciphers") or []
            folder_obj = self._validate_folder(user=user, folder=folder)
            folder_ciphers = json.loads(json.dumps(folder_ciphers))

        new_sharing, existed_member_users, non_existed_member_users = self.sharing_repository.create_new_sharing(
            sharing_key=sharing_key, members=members, groups=groups,
            cipher=cipher_obj, shared_cipher_data=shared_cipher_data,
            folder=folder_obj, shared_collection_name=folder_name, shared_collection_ciphers=folder_ciphers
        )
        return new_sharing, existed_member_users, non_existed_member_users

    def share_multiple_ciphers_or_folders(self, user: User, sharing_key: str, ciphers: List, folders: List,
                                          owner_name: str = None, ip: str = None) -> Dict:
        # First, validate members and groups
        if ciphers:
            for cipher in ciphers:
                self._validate_share_groups(user=user, groups=cipher.get("groups"))
        if folders:
            for folder in folders:
                self._validate_share_groups(user=user, groups=folder.get("groups"))

        existed_member_users = []
        non_existed_member_users = []
        user_enterprise_ids = self.enterprise_repository.list_user_enterprise_ids(user_id=user.user_id, **{
            "status": E_MEMBER_STATUS_CONFIRMED
        })

        # Start sharing ciphers
        shared_cipher_ids = []
        if ciphers:
            for cipher_member in ciphers:
                members = cipher_member.get("members") or []
                cipher = cipher_member.get("cipher")
                try:
                    new_sharing, existed_members, non_existed_members = self._share_cipher_or_folder(
                        user=user, sharing_key=sharing_key,
                        members=members,
                        groups=cipher_member.get("groups") or [],
                        cipher=cipher,
                        shared_cipher_data=cipher_member.get("shared_cipher_data"),
                        folder=None
                    )
                except (CipherDoesNotExistException, CipherBelongCollectionException, CipherBelongTeamException,
                        FolderDoesNotExistException):
                    continue
                if user_enterprise_ids:
                    emails = [m.get("email") for m in members]
                    BackgroundFactory.get_background(bg_name=BG_EVENT).run(
                        func_name="create_by_enterprise_ids", **{
                            "enterprise_ids": user_enterprise_ids, "user_id": user.user_id,
                            "acting_user_id": user.user_id,
                            "type": EVENT_ITEM_SHARE_CREATED, "ip_address": ip,
                            "cipher_id": cipher.get("id"),
                            "metadata": {
                                "item_type": MAP_CIPHER_TYPE_STR.get(cipher.get("type")),
                                "emails": emails
                            }
                        })
                existed_member_users += existed_members
                non_existed_member_users += non_existed_members
                shared_cipher_ids.append(cipher.get("id"))

        # Sharing folders
        if folders:
            for folder in folders:
                members = folder.get("members") or []
                try:
                    new_sharing, existed_members, non_existed_members = self._share_cipher_or_folder(
                        user=user, sharing_key=sharing_key,
                        members=members,
                        groups=folder.get("groups") or [],
                        cipher=None,
                        shared_cipher_data=None,
                        folder=folder
                    )
                except (CipherDoesNotExistException, CipherBelongCollectionException, CipherBelongTeamException,
                        FolderDoesNotExistException):
                    continue
                # Create activity logs
                if user_enterprise_ids:
                    emails = [m.get("email") for m in members]
                    BackgroundFactory.get_background(bg_name=BG_EVENT).run(
                        func_name="create_by_enterprise_ids", **{
                            "enterprise_ids": user_enterprise_ids, "user_id": user.user_id,
                            "acting_user_id": user.user_id,
                            "type": EVENT_ITEM_SHARE_CREATED, "ip_address": ip,
                            "metadata": {"item_type": "folder", "emails": emails}
                        })
                existed_member_users += existed_members
                non_existed_member_users += non_existed_members

        # Sync the invitation
        share_type = "folder" if folders else "cipher"
        sync_user_ids = existed_member_users + [user.user_id]
        # Sync member invitation
        for u_id in sync_user_ids:
            self.user_repository.delete_sync_cache_data(user_id=u_id)
        PwdSync(event=SYNC_EVENT_MEMBER_INVITATION, user_ids=sync_user_ids).send()
        PwdSync(event=SYNC_EVENT_CIPHER_INVITATION, user_ids=existed_member_users).send()
        # Sync ciphers
        if share_type == "cipher":
            PwdSync(event=SYNC_EVENT_CIPHER_SHARE, user_ids=[user.user_id]).send(data={"ids": shared_cipher_ids})
        else:
            PwdSync(event=SYNC_EVENT_CIPHER, user_ids=sync_user_ids).send()

        # Get notification user: Mail and notification
        mail_user_ids = self.notification_setting_repository.get_user_mail(
            category_id=NOTIFY_SHARING, user_ids=existed_member_users
        )
        notification_user_ids = self.notification_setting_repository.get_user_notification(
            category_id=NOTIFY_SHARING, user_ids=existed_member_users
        )
        # Send mobile notification
        fcm_ids = self.device_repository.get_fcm_ids_by_user_ids(user_ids=notification_user_ids)
        fcm_message = FCMRequestEntity(
            fcm_ids=fcm_ids, priority="high",
            data={
                "event": FCM_TYPE_NEW_SHARE,
                "data": {
                    "pwd_user_ids": notification_user_ids,
                    "count": len(ciphers),
                    "owner_name": owner_name
                }
            }
        )
        FCMSenderService(is_background=True).run("send_message", **{"fcm_message": fcm_message})

        return {
            "shared_type_name": share_type,
            "non_existed_member_users": non_existed_member_users,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids,
        }

    def invitation_confirm(self, user: User, sharing_invitation: TeamMember, key: str):
        member = self.sharing_repository.confirm_invitation(member=sharing_invitation, key=key)
        sharing_id = member.team.team_id

        # Sending notification
        shared_type_name = None
        item_id = None
        cipher_id = None
        folder_id = None

        if not self.is_folder_sharing(sharing_id=sharing_id):
            share_cipher = self.sharing_repository.get_share_cipher(sharing_id=sharing_id)
            if share_cipher:
                shared_type_name = share_cipher.cipher_type
                item_id = share_cipher.cipher_id
                cipher_id = item_id
        # Else, share a folder
        else:
            share_collection = self.sharing_repository.get_share_collection(sharing_id=sharing_id)
            if share_collection:
                shared_type_name = "folder"
                item_id = share_collection.collection_id
                folder_id = item_id

        if cipher_id:
            PwdSync(event=SYNC_EVENT_CIPHER_SHARE, user_ids=[member.user.user_id]).send(data={
                "ids": [cipher_id], "id": cipher_id
            })
        else:
            PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[member.user.user_id]).send()
        PwdSync(event=SYNC_EVENT_MEMBER_CONFIRMED, user_ids=[member.user.user_id, user.user_id]).send()

        mail_user_ids = self.notification_setting_repository.get_user_mail(
            category_id=NOTIFY_SHARING, user_ids=[member.user.user_id]
        )
        notification_user_ids = self.notification_setting_repository.get_user_notification(
            category_id=NOTIFY_SHARING, user_ids=[member.user.user_id]
        )
        fcm_ids = self.device_repository.get_fcm_ids_by_user_ids(user_ids=notification_user_ids)
        fcm_message = FCMRequestEntity(
            fcm_ids=list(fcm_ids), priority="high",
            data={
                "event": FCM_TYPE_NEW_SHARE_AFTER_OWNER_CONFIRMED,
                "data": {
                    "id": member.team_id,
                    "share_type": shared_type_name,
                    "pwd_user_ids": [member.user.user_id],
                }
            }
        )
        FCMSenderService(is_background=True).run("send_message", **{"fcm_message": fcm_message})
        return {
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids,
            "share_type": shared_type_name,
            "item_id": item_id,
            "folder_id": folder_id,
            "cipher_id": cipher_id
        }

    def update_role_invitation(self, member: TeamMember, role_id: str, hide_passwords: bool = None) -> TeamMember:
        member = self.sharing_repository.update_role_invitation(
            member=member, role_id=role_id, hide_passwords=hide_passwords
        )
        if not member:
            raise TeamMemberDoesNotExistException
        sharing_id = member.team.team_id
        primary_member = self.team_member_repository.get_primary_member(team_id=sharing_id)
        sync_user_ids = [member.user.user_id, primary_member.user.user_id] if member.user else \
            [primary_member.user.user_id]
        PwdSync(event=SYNC_EVENT_MEMBER_UPDATE, user_ids=sync_user_ids).send()
        if self.is_folder_sharing(sharing_id=sharing_id) is False:
            share_cipher = self.sharing_repository.get_share_cipher(sharing_id=sharing_id)
            PwdSync(event=SYNC_EVENT_CIPHER_SHARE, user_ids=[member.user.user_id] if member.user else []).send(
                data={"id": share_cipher.cipher_id, "ids": [share_cipher.cipher_id]}
            )
        # Else, share a folder
        else:
            share_collection = self.sharing_repository.get_share_collection(sharing_id=sharing_id)
            PwdSync(event=SYNC_EVENT_COLLECTION_UPDATE, user_ids=[member.user.user_id] if member.user else []).send(
                data={"id": share_collection.collection_id}
            )
        return member

    def invitation_group_confirm(self, user: User, sharing: Team, group_id: str, members: List):
        group = self.team_group_repository.get_share_group_by_enterprise_group_id(
            sharing_id=sharing.team_id, enterprise_group_id=group_id
        )
        if not group:
            raise TeamGroupDoesNotExistException
        members_user_ids = [member_data.get("user_id") for member_data in members if member_data.get("user_id")]
        # Get list group members that were invited
        invited_members = self.team_group_repository.list_group_members(group_id=group.group_id, **{
            "statuses": [PM_MEMBER_STATUS_ACCEPTED, PM_MEMBER_STATUS_INVITED],
            "user_ids": members_user_ids
        })
        for invited_member in invited_members:
            member_data = next(
                (item for item in members if item["user_id"] == invited_member.member.user.user_id), None
            )
            if member_data and member_data.get("key"):
                self.sharing_repository.confirm_invitation(member=invited_member.member, key=member_data.get("key"))
        PwdSync(event=SYNC_EVENT_CIPHER, user_ids=members_user_ids).send()
        PwdSync(event=SYNC_EVENT_MEMBER_CONFIRMED, user_ids=members_user_ids + [user.user_id]).send()

    def update_group_role(self, sharing: Team, group_id: str, role_id: str) -> Group:
        sharing_id = sharing.team_id
        group = self.team_group_repository.get_share_group_by_enterprise_group_id(
            sharing_id=sharing_id, enterprise_group_id=group_id
        )
        if not group:
            raise TeamGroupDoesNotExistException
        group = self.team_group_repository.update_group_role_invitation(
            group=group, role_id=role_id
        )
        if not group:
            raise TeamGroupDoesNotExistException

        primary_member = self.team_member_repository.get_primary_member(team_id=sharing_id)
        group_members_user_ids = self.team_group_repository.list_group_members_user_ids(group_id=group_id)

        PwdSync(event=SYNC_EVENT_MEMBER_UPDATE, user_ids=group_members_user_ids + [primary_member.user.user_id]).send()
        if self.is_folder_sharing(sharing_id=sharing_id) is False:
            share_cipher = self.sharing_repository.get_share_cipher(sharing_id=sharing_id)
            PwdSync(event=SYNC_EVENT_CIPHER_SHARE, user_ids=group_members_user_ids).send(
                data={"ids": [share_cipher.cipher_id], "id": share_cipher.cipher_id}
            )
        # Else, share a folder
        else:
            share_collection = self.sharing_repository.get_share_collection(sharing_id=sharing_id)
            PwdSync(event=SYNC_EVENT_COLLECTION_UPDATE, user_ids=group_members_user_ids).send(
                data={"id": share_collection.collection_id}
            )
        return group

    def list_my_share(self, user_id: int, type_param: str = None) -> List:
        my_shared_teams = []
        personal_shared_teams = self.sharing_repository.list_my_personal_share_teams(user_id=user_id, **{
            "type": type_param
        })
        for personal_shared_team in personal_shared_teams:
            shared_members = self.team_member_repository.list_member_by_teams(
                teams=[personal_shared_team], exclude_owner=True, is_added_by_group=False
            )
            shared_members_data = []
            for member in shared_members:
                member_data = {
                    "id": member.team_member_id,
                    "access_time": member.access_time,
                    "email": member.email,


                    "role": member.role.name,
                    "status": member.status,
                    "hide_passwords": member.hide_passwords,
                    "share_type": self.get_personal_share_type(member=member),
                    "pwd_user_id": member.user.internal_id if member.user else None
                }
                try:
                    if member.user is not None:
                        member_data.update({
                            "email": member.user.email,
                            "full_name": member.user.full_name,
                            "username": member.user.username,
                            "avatar": member.user.get_avatar()
                        })
                    else:
                        member_data.update({
                            "avatar": get_avatar(member.email)
                        })
                except AttributeError:
                    member_data.update({
                        "user_id": member.user.user_id if member.user else None,
                    })

                shared_members_data.append(member_data)

            shared_groups = self.team_group_repository.list_groups_by_sharing_id(sharing_id=personal_shared_team.team_id)
            shared_groups_data = []
            for group in shared_groups:
                shared_groups_data.append({
                    "id": group.enterprise_group.enterprise_group_id if group.enterprise_group else None,
                    "name": group.name,
                    "access_time": group.creation_date,
                    "role": group.role.name,
                    "share_type": self.get_personal_share_type(role=group.role.name),
                })
            team_data = {
                "id": personal_shared_team.team_id,
                "name": personal_shared_team.name,
                "description": personal_shared_team.description,
                "organization_id": personal_shared_team.team_id,
                "members": shared_members_data,
                "groups": shared_groups_data
            }
            my_shared_teams.append(team_data)
        return my_shared_teams

    def stop_share(self, user: User, sharing: Team, member_id: str = None, group_id: str = None,
                   cipher: Dict = None, personal_cipher_data: Dict = None, folder: Dict = None):
        sharing_id = sharing.team_id

        group = None
        if group_id:
            group = self.team_group_repository.get_share_group_by_enterprise_group_id(
                sharing_id=sharing_id, enterprise_group_id=group_id
            )
            if not group:
                raise TeamGroupDoesNotExistException
        member = None
        if member_id:
            member = self.team_member_repository.get_team_member_by_id(team_member_id=member_id)
            if not member and member.user.user_id == user.user_id or member.team.team_id != sharing_id:
                raise TeamMemberDoesNotExistException

        shared_team = group.team if group else member.team

        cipher_obj = None
        collection_obj = None
        folder_name = None
        folder_ciphers = None

        # If stop share cipher
        if cipher:
            cipher_obj = self._validate_stop_cipher(sharing_id=shared_team.team_id, cipher=cipher)
            personal_cipher_data = json.loads(json.dumps(personal_cipher_data))

        # If stop share folder
        if folder:
            folder_name = folder.get("name")
            folder_ciphers = folder.get("ciphers") or []
            collection_obj = self._validate_stop_folder(sharing_id=shared_team.team_id, folder=folder)
            folder_ciphers = json.loads(json.dumps(folder_ciphers))

        removed_member_user_ids = self.sharing_repository.stop_sharing(
            member=member, group=group,
            cipher=cipher_obj, cipher_data=personal_cipher_data,
            collection=collection_obj, personal_folder_name=folder_name, personal_folder_ciphers=folder_ciphers
        )
        PwdSync(event=SYNC_EVENT_MEMBER_REMOVE, user_ids=[user.user_id] + removed_member_user_ids).send()
        # Re-sync data of the owner and removed member
        if cipher_obj:
            PwdSync(
                event=SYNC_EVENT_CIPHER_SHARE, user_ids=[user.user_id] + removed_member_user_ids
            ).send(data={"id": cipher_obj.cipher_id, "ids": [cipher_obj.cipher_id]})
        if collection_obj:
            PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[user.user_id] + removed_member_user_ids).send()
        # Delete cached data
        for u_id in [user.user_id] + removed_member_user_ids:
            self.user_repository.delete_sync_cache_data(user_id=u_id)

    def leave_sharing_team(self, user: User, sharing: Team):
        member = self.team_member_repository.get_user_team_member(user_id=user.user_id, team_id=sharing.team_id)
        if not member or member.role.name == MEMBER_ROLE_OWNER:
            raise TeamMemberDoesNotExistException

        member_user_id = self.sharing_repository.leave_sharing(member=member)
        # Re-sync data of the member
        # If share a cipher
        sharing_id = sharing.team_id
        if self.is_folder_sharing(sharing_id=sharing_id) is False:
            share_cipher = self.sharing_repository.get_share_cipher(sharing_id=sharing_id)
            self.user_repository.delete_sync_cache_data(user_id=member_user_id)
            PwdSync(event=SYNC_EVENT_CIPHER_SHARE, user_ids=[member_user_id], team=sharing, add_all=True).send(data={
                "id": share_cipher.cipher_id, "ids": [share_cipher.cipher_id]
            })
        # Else, share a folder
        else:
            share_collection = self.sharing_repository.get_share_collection(sharing_id=sharing_id)
            self.user_repository.delete_sync_cache_data(user_id=user.user_id)
            PwdSync(event=SYNC_EVENT_COLLECTION_UPDATE, user_ids=[user.user_id], team=sharing, add_all=True).send(
                data={"id": share_collection.collection_id}
            )

    def stop_share_cipher_folder(self, user: User, sharing: Team,
                                 cipher: Dict = None, personal_cipher_data: Dict = None, folder: Dict = None):
        sharing_id = sharing.team_id
        cipher_obj = None
        collection_obj = None
        folder_name = None
        folder_ciphers = None

        # If stop share cipher
        if cipher:
            cipher_obj = self._validate_stop_cipher(sharing_id=sharing_id, cipher=cipher)
            personal_cipher_data = json.loads(json.dumps(personal_cipher_data))

        # If stop share folder
        if folder:
            folder_name = folder.get("name")
            folder_ciphers = folder.get("ciphers") or []
            collection_obj = self._validate_stop_folder(sharing_id=sharing_id, folder=folder)
            folder_ciphers = json.loads(json.dumps(folder_ciphers))

        removed_members_user_id, personal_folder_id = self.sharing_repository.stop_share_all_members(
            team_id=sharing_id,
            cipher=cipher_obj, cipher_data=personal_cipher_data,
            collection=collection_obj, personal_folder_name=folder_name, personal_folder_ciphers=folder_ciphers
        )

        PwdSync(event=SYNC_EVENT_MEMBER_REMOVE, user_ids=[user.user_id] + removed_members_user_id).send()
        # Re-sync data of the owner and removed member
        if cipher_obj:
            PwdSync(event=SYNC_EVENT_CIPHER_SHARE, user_ids=[user.user_id] + removed_members_user_id).send(
                data={"id": cipher_obj.cipher_id, "ids": [cipher_obj.cipher_id]}
            )
        if collection_obj:
            PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[user.user_id] + removed_members_user_id).send()

        return personal_folder_id

    def add_member(self, user: User, sharing: Team, members: List = None, groups: List = None):
        sharing_id = sharing.team_id
        # First, validate members and groups
        groups = self._validate_share_groups(user=user, groups=groups)
        share_folder = self.sharing_repository.get_share_collection(sharing_id=sharing_id)
        if not share_folder:
            raise CollectionDoesNotExistException

        existed_member_users, non_existed_member_users = self.sharing_repository.add_members(
            team_id=sharing_id, shared_collection_id=share_folder.collection_id, members=members, groups=groups
        )
        for u_id in existed_member_users + [user.user_id]:
            self.user_repository.delete_sync_cache_data(user_id=u_id)
        PwdSync(event=SYNC_EVENT_MEMBER_INVITATION, user_ids=existed_member_users + [user.user_id]).send()

        mail_user_ids = self.notification_setting_repository.get_user_mail(
            category_id=NOTIFY_SHARING, user_ids=existed_member_users
        )
        notification_user_ids = self.notification_setting_repository.get_user_notification(
            category_id=NOTIFY_SHARING, user_ids=existed_member_users
        )
        return {
            "id": sharing_id,
            "shared_type_name": "folder",
            "non_existed_member_users": non_existed_member_users,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        }

    def update_share_folder(self, user: User, sharing: Team, folder_id: str, new_name: str) -> Optional[Collection]:
        sharing_id = sharing.team_id
        collection = self.team_repository.get_team_collection_by_id(team_id=sharing_id, collection_id=folder_id)
        if not collection:
            raise CollectionDoesNotExistException

        collection = self.sharing_repository.update_share_folder(collection=collection, name=new_name)
        self.user_repository.delete_sync_cache_data(user_id=user.user_id)
        PwdSync(event=SYNC_EVENT_COLLECTION_UPDATE, user_ids=[user.user_id], team=sharing, add_all=True).send(
            data={"id": collection.collection_id}
        )
        return collection

    def delete_share_folder(self, user: User, sharing: Team, folder: Dict):
        sharing_id = sharing.team_id
        folder_name = folder.get("name")
        folder_ciphers = folder.get("ciphers") or []
        collection_obj = self._validate_stop_folder(sharing_id=sharing_id, folder=folder)
        folder_ciphers = json.loads(json.dumps(folder_ciphers))
        removed_members_user_id = self.sharing_repository.delete_share_folder(
            collection=collection_obj, personal_folder_name=folder_name, personal_folder_ciphers=folder_ciphers
        )
        PwdSync(event=SYNC_EVENT_MEMBER_REMOVE, user_ids=[user.user_id] + removed_members_user_id).send()
        PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[user.user_id] + removed_members_user_id).send()

    def stop_share_folder(self, user: User, sharing: Team, folder: Dict):
        sharing_id = sharing.team_id
        folder_name = folder.get("name")
        folder_ciphers = folder.get("ciphers") or []
        collection_obj = self._validate_stop_folder(sharing_id=sharing_id, folder=folder)
        folder_ciphers = json.loads(json.dumps(folder_ciphers))

        removed_members_user_id, personal_folder_id = self.sharing_repository.stop_share_all_members(
            team_id=sharing_id,
            collection=collection_obj, personal_folder_name=folder_name, personal_folder_ciphers=folder_ciphers
        )
        PwdSync(event=SYNC_EVENT_MEMBER_REMOVE, user_ids=[user.user_id] + removed_members_user_id).send()
        PwdSync(event=SYNC_EVENT_CIPHER, user_ids=[user.user_id] + removed_members_user_id).send()
        return personal_folder_id

    def add_item_share_folder(self, user: User, sharing: Team, folder_id: str, cipher: Dict):
        sharing_id = sharing.team_id
        collection_obj = self.team_repository.get_team_collection_by_id(team_id=sharing_id, collection_id=folder_id)
        if not collection_obj:
            raise CollectionDoesNotExistException

        cipher_obj = self.cipher_repository.get_by_id(cipher_id=cipher.get("id"))
        if not cipher_obj or (cipher_obj.user and cipher_obj.user.user_id != user.user_id):
            raise CipherDoesNotExistException
        if cipher_obj.team:
            raise CipherBelongTeamException
        cipher["team_id"] = sharing_id
        cipher["collection_ids"] = [collection_obj.collection_id]
        cipher["user_id"] = user.user_id
        cipher_data = json.loads(json.dumps(cipher))

        cipher_obj = self.cipher_repository.update_cipher(cipher_id=cipher_obj.cipher_id, cipher_data=cipher_data)
        self.sharing_repository.update_share_folder(
            collection=collection_obj, name=collection_obj.name, revision_date=now()
        )
        self.user_repository.delete_sync_cache_data(user_id=user.user_id)
        # PwdSync(
        #     event=SYNC_EVENT_CIPHER_UPDATE, user_ids=[user.user_id], team=sharing, add_all=True
        # ).send(data={"id": cipher_obj.cipher_id})
        PwdSync(
            event=SYNC_EVENT_CIPHER_SHARE, user_ids=[user.user_id], team=sharing, add_all=True
        ).send(data={"id": cipher_obj.cipher_id, "ids": [cipher_obj.cipher_id]})

    def remove_item_share_folder(self, user: User, sharing: Team, folder_id: str, cipher: Dict):
        sharing_id = sharing.team_id
        collection_obj = self.team_repository.get_team_collection_by_id(team_id=sharing_id, collection_id=folder_id)
        if not collection_obj:
            raise CollectionDoesNotExistException

        cipher_obj = self.cipher_repository.get_by_id(cipher_id=cipher.get("id"))
        if not cipher_obj or collection_obj.team.team_id != sharing_id:
            raise CipherDoesNotExistException

        cipher["team_id"] = None
        cipher["collection_ids"] = []
        cipher["user_id"] = user.user_id
        cipher_data = json.loads(json.dumps(cipher))
        cipher_obj = self.cipher_repository.update_cipher(cipher_id=cipher_obj.cipher_id, cipher_data=cipher_data)
        self.sharing_repository.update_share_folder(
            collection=collection_obj, name=collection_obj.name, revision_date=now()
        )
        self.user_repository.delete_sync_cache_data(user_id=user.user_id)
        PwdSync(event=SYNC_EVENT_CIPHER_SHARE, user_ids=[user.user_id], team=sharing, add_all=True).send(
            data={"id": cipher_obj.cipher_id, "ids": [cipher_obj.cipher_id]}
        )

    def add_group_member_to_share(self, enterprise_group: EnterpriseGroup, new_member_ids: List[str]):
        confirmed_data = self.sharing_repository.add_group_member_to_share(
            enterprise_group=enterprise_group, new_member_ids=new_member_ids
        )
        return confirmed_data
