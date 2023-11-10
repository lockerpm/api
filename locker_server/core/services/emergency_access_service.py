from typing import List, Optional

from locker_server.core.entities.emergency_access.emergency_access import EmergencyAccess
from locker_server.core.entities.user.user import User
from locker_server.core.exceptions.emergency_access_exception import EmergencyAccessDoesNotExistException, \
    EmergencyAccessGranteeExistedException, EmergencyAccessEmailExistedException
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.core.repositories.cipher_repository import CipherRepository
from locker_server.core.repositories.device_repository import DeviceRepository
from locker_server.core.repositories.emergency_access_repository import EmergencyAccessRepository
from locker_server.core.repositories.notification_setting_repository import NotificationSettingRepository
from locker_server.core.repositories.team_member_repository import TeamMemberRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.constants.emergency_access import *
from locker_server.shared.constants.members import PM_MEMBER_STATUS_CONFIRMED, MEMBER_ROLE_OWNER
from locker_server.shared.constants.user_notification import NOTIFY_EMERGENCY_ACCESS, NOTIFY_CHANGE_MASTER_PASSWORD
from locker_server.shared.external_services.fcm.constants import FCM_TYPE_EMERGENCY_REJECT_INVITATION, \
    FCM_TYPE_EMERGENCY_INVITE, FCM_TYPE_EMERGENCY_ACCEPT_INVITATION, FCM_TYPE_EMERGENCY_INITIATE, \
    FCM_TYPE_EMERGENCY_REJECT_REQUEST, FCM_TYPE_EMERGENCY_APPROVE_REQUEST
from locker_server.shared.external_services.fcm.fcm_request_entity import FCMRequestEntity
from locker_server.shared.external_services.fcm.fcm_sender import FCMSenderService
from locker_server.shared.external_services.pm_sync import PwdSync, SYNC_EMERGENCY_ACCESS


class EmergencyAccessService:
    """
    This class represents Use Cases related Emergency Access
    """

    def __init__(self, emergency_access_repository: EmergencyAccessRepository,
                 device_repository: DeviceRepository,
                 notification_setting_repository: NotificationSettingRepository,
                 user_repository: UserRepository,
                 cipher_repository: CipherRepository,
                 team_member_repository: TeamMemberRepository):
        self.emergency_access_repository = emergency_access_repository
        self.device_repository = device_repository
        self.notification_setting_repository = notification_setting_repository
        self.user_repository = user_repository
        self.cipher_repository = cipher_repository
        self.team_member_repository = team_member_repository

    def get_by_id(self, emergency_access_id: str) -> Optional[EmergencyAccess]:
        emergency_access = self.emergency_access_repository.get_by_id(emergency_access_id=emergency_access_id)
        if not emergency_access:
            raise EmergencyAccessDoesNotExistException
        return emergency_access

    def send_mobile_notification(self, notification_user_ids, event, data):
        if not notification_user_ids:
            return
        fcm_ids = self.device_repository.get_fcm_ids_by_user_ids(user_ids=notification_user_ids)
        fcm_message = FCMRequestEntity(
            fcm_ids=list(fcm_ids), priority="high",
            data={"event": event, "data": data}
        )
        FCMSenderService(is_background=True).run("send_message", **{"fcm_message": fcm_message})

    def list_by_grantor_id(self, grantor_id: int) -> List[EmergencyAccess]:
        return self.emergency_access_repository.list_by_grantor_id(grantor_id=grantor_id)

    def list_by_grantee_id(self, grantee_id: int) -> List[EmergencyAccess]:
        return self.emergency_access_repository.list_by_grantee_id(grantee_id=grantee_id)

    def destroy_emergency_access(self, user: User, emergency_access: EmergencyAccess, full_name: str = None):
        if not full_name:
            full_name = user.full_name
        status = emergency_access.status
        grantor_user_id = emergency_access.grantor.user_id
        grantee_user_id = emergency_access.grantee.user_id if emergency_access.grantee else None

        mail_user_ids = self.notification_setting_repository.get_user_mail(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantor_user_id, grantee_user_id]
        )
        notification_user_ids = self.notification_setting_repository.get_user_notification(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantor_user_id, grantee_user_id]
        )

        # Send mobile notification
        if status == EMERGENCY_ACCESS_STATUS_INVITED and user.user_id == grantee_user_id \
                and grantor_user_id in notification_user_ids:
            self.send_mobile_notification(
                notification_user_ids=[grantor_user_id], event=FCM_TYPE_EMERGENCY_REJECT_INVITATION,
                data={
                    "id": emergency_access.emergency_access_id,
                    "type": emergency_access.emergency_access_type,
                    "grantee_name": full_name,
                    "is_grantor": True,
                }
            )
        self.emergency_access_repository.destroy_emergency_access(
            emergency_access_id=emergency_access.emergency_access_id
        )
        return {
            "grantor_user_id": grantor_user_id,
            "grantee_user_id": grantee_user_id,
            "status": status,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        }

    def invite_emergency_access(self, grantor: User, emergency_access_type: str, wait_time_days: int, key: str = None,
                                grantee_id: int = None,  email: str = None,
                                grantor_fullname: str = None) -> Optional[EmergencyAccess]:
        grantor_fullname = grantor_fullname or grantor.full_name
        if grantee_id:
            grantee = self.user_repository.get_user_by_id(user_id=grantee_id)
            if not grantee:
                raise UserDoesNotExistException
            if self.emergency_access_repository.check_emergency_existed(
                grantor_id=grantor.user_id, emergency_access_type=emergency_access_type, grantee_id=grantee_id
            ) is True:
                raise EmergencyAccessGranteeExistedException

        else:
            if self.emergency_access_repository.check_emergency_existed(
                grantor_id=grantor.user_id, emergency_access_type=emergency_access_type, email=email
            ) is True:
                raise EmergencyAccessEmailExistedException

        new_emergency_access = self.emergency_access_repository.invite_emergency_access(
            grantor_id=grantor.user_id,
            emergency_access_type=emergency_access_type,
            wait_time_days=wait_time_days,
            grantee_id=grantee_id,
            email=email,
            key=key
        )
        # Send notification via ws for grantee
        mail_user_ids = []
        notification_user_ids = []
        if new_emergency_access.grantee:
            PwdSync(event=SYNC_EMERGENCY_ACCESS, user_ids=[new_emergency_access.grantee.user_id]).send()
            mail_user_ids = self.notification_setting_repository.get_user_mail(
                category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[new_emergency_access.grantee.user_id]
            )
            notification_user_ids = self.notification_setting_repository.get_user_notification(
                category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[new_emergency_access.grantee.user_id]
            )
            # Send mobile notification
            self.send_mobile_notification(
                notification_user_ids=notification_user_ids, event=FCM_TYPE_EMERGENCY_INVITE,
                data={
                    "id": new_emergency_access.emergency_access_id,
                    "type": new_emergency_access.emergency_access_type,
                    "grantor_name": grantor_fullname,
                    "is_grantee": True
                }
            )
        return new_emergency_access, mail_user_ids, notification_user_ids

    def reinvite_emergency_access(self, emergency_access: EmergencyAccess, grantor_fullname=None):
        grantor_fullname = grantor_fullname or emergency_access.grantor.full_name
        if emergency_access.grantee:
            PwdSync(event=SYNC_EMERGENCY_ACCESS, user_ids=[emergency_access.grantee.user_id]).send()
        grantee_user_id = emergency_access.grantee.user_id if emergency_access.grantee else None
        mail_user_ids = []
        notification_user_ids = []
        if grantee_user_id:
            mail_user_ids = self.notification_setting_repository.get_user_mail(
                category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
            )
            notification_user_ids = self.notification_setting_repository.get_user_notification(
                category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
            )
            # Send mobile notification
            self.send_mobile_notification(
                notification_user_ids=notification_user_ids, event=FCM_TYPE_EMERGENCY_INVITE,
                data={
                    "id": emergency_access.emergency_access_id,
                    "type": emergency_access.emergency_access_type,
                    "grantor_name": grantor_fullname,
                    "is_grantee": True
                }
            )
        return emergency_access, mail_user_ids, notification_user_ids

    def accept_emergency_access(self, emergency_access: EmergencyAccess, grantee_fullname=None):
        if emergency_access.status != EMERGENCY_ACCESS_STATUS_INVITED:
            raise EmergencyAccessDoesNotExistException
        if emergency_access.key_encrypted:
            emergency_access = self.emergency_access_repository.confirm_emergency_access(
                emergency_access, emergency_access.key_encrypted
            )
        else:
            emergency_access = self.emergency_access_repository.accept_emergency_access(emergency_access)

        grantor_user_id = emergency_access.grantor.user_id
        grantee_user_id = emergency_access.grantee.user_id if emergency_access.grantee else None
        mail_user_ids = self.notification_setting_repository.get_user_mail(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantor_user_id, grantee_user_id]
        )
        notification_user_ids = self.notification_setting_repository.get_user_notification(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantor_user_id, grantee_user_id]
        )

        if emergency_access.status == EMERGENCY_ACCESS_STATUS_CONFIRMED and grantor_user_id in notification_user_ids:
            # Send mobile notification
            self.send_mobile_notification(
                notification_user_ids=[grantor_user_id], event=FCM_TYPE_EMERGENCY_ACCEPT_INVITATION,
                data={
                    "id": emergency_access.emergency_access_id,
                    "type": emergency_access.emergency_access_type,
                    "grantee_name": grantee_fullname,
                    "is_grantor": True,
                }
            )

        return {
            "success": True,
            "grantor_user_id": grantor_user_id,
            "grantee_user_id": grantee_user_id,
            "grantee_email": emergency_access.email,
            "status": emergency_access.status,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        }

    def confirm_emergency_access(self, emergency_access: EmergencyAccess, key: str = None):
        if emergency_access.status != EMERGENCY_ACCESS_STATUS_ACCEPTED:
            raise EmergencyAccessDoesNotExistException
        self.emergency_access_repository.confirm_emergency_access(emergency_access, key_encrypted=key)
        grantee_user_id = emergency_access.grantee.user_id if emergency_access.grantee else None
        mail_user_ids = self.notification_setting_repository.get_user_mail(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
        )
        notification_user_ids = self.notification_setting_repository.get_user_notification(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
        )
        return {
            "grantee_user_id": grantee_user_id,
            "grantee_email": emergency_access.email,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        }

    def initiate_emergency_access(self, emergency_access: EmergencyAccess, grantee_fullname=None):
        if emergency_access.status != EMERGENCY_ACCESS_STATUS_CONFIRMED:
            raise EmergencyAccessDoesNotExistException
        self.emergency_access_repository.initiate_emergency_access(emergency_access)
        mail_user_ids = self.notification_setting_repository.get_user_mail(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[emergency_access.grantor.user_id]
        )
        notification_user_ids = self.notification_setting_repository.get_user_notification(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[emergency_access.grantor.user_id]
        )
        # Send mobile notification
        self.send_mobile_notification(
            notification_user_ids=notification_user_ids, event=FCM_TYPE_EMERGENCY_INITIATE,
            data={
                "id": emergency_access.emergency_access_id,
                "type": emergency_access.emergency_access_type,
                "grantee_name": grantee_fullname,
                "is_grantor": True,
            }
        )
        return {
            "type": emergency_access.emergency_access_type,
            "status": emergency_access.status,
            "approve_after": emergency_access.wait_time_days,
            "grantor_user_id": emergency_access.grantor.user_id,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        }

    def reject_emergency_access(self, emergency_access: EmergencyAccess, grantor_fullname=None):
        if emergency_access.status not in [EMERGENCY_ACCESS_STATUS_RECOVERY_INITIATED,
                                           EMERGENCY_ACCESS_STATUS_RECOVERY_APPROVED]:
            raise EmergencyAccessDoesNotExistException
        self.emergency_access_repository.reject_emergency_access(emergency_access)
        grantee_user_id = emergency_access.grantee.user_id if emergency_access.grantee else None
        mail_user_ids = self.notification_setting_repository.get_user_mail(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
        )
        notification_user_ids = self.notification_setting_repository.get_user_notification(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
        )
        # Send mobile notification
        self.send_mobile_notification(
            notification_user_ids=notification_user_ids, event=FCM_TYPE_EMERGENCY_REJECT_REQUEST,
            data={
                "id": emergency_access.emergency_access_id,
                "type": emergency_access.emergency_access_type,
                "grantor_name": grantor_fullname,
                "is_grantee": True,
            }
        )
        return {
            "grantee_user_id": grantee_user_id,
            "grantee_email": emergency_access.email,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        }

    def approve_emergency_access(self, emergency_access: EmergencyAccess, grantor_fullname=None):
        if emergency_access.status != EMERGENCY_ACCESS_STATUS_RECOVERY_INITIATED:
            raise EmergencyAccessDoesNotExistException
        self.emergency_access_repository.approve_emergency_access(emergency_access)
        grantee_user_id = emergency_access.grantee.user_id if emergency_access.grantee else None
        mail_user_ids = self.notification_setting_repository.get_user_mail(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
        )
        notification_user_ids = self.notification_setting_repository.get_user_notification(
            category_id=NOTIFY_EMERGENCY_ACCESS, user_ids=[grantee_user_id]
        )
        # Send mobile notification
        self.send_mobile_notification(
            notification_user_ids=notification_user_ids, event=FCM_TYPE_EMERGENCY_APPROVE_REQUEST,
            data={
                "id": emergency_access.emergency_access_id,
                "type": emergency_access.emergency_access_type,
                "grantor_name": grantor_fullname,
                "is_grantee": True,
            }
        )
        return {
            "grantee_user_id": grantee_user_id,
            "grantee_email": emergency_access.email,
            "mail_user_ids": mail_user_ids,
            "notification_user_ids": notification_user_ids
        }

    def view_emergency_access(self, emergency_access: EmergencyAccess):
        if emergency_access.emergency_access_type != EMERGENCY_ACCESS_TYPE_VIEW or \
                emergency_access.status != EMERGENCY_ACCESS_STATUS_RECOVERY_APPROVED:
            raise EmergencyAccessDoesNotExistException
        ciphers = self.cipher_repository.get_multiple_by_user(
            user_id=emergency_access.grantor.user_id
        )
        team_members = self.team_member_repository.list_members_by_user_id(
            user_id=emergency_access.grantor.user_id, **{
                "statuses": [PM_MEMBER_STATUS_CONFIRMED],
                "team_key_null": False
            }
        )
        return ciphers, team_members

    def takeover_emergency_access(self, emergency_access: EmergencyAccess):
        if emergency_access.emergency_access_type != EMERGENCY_ACCESS_TYPE_TAKEOVER or \
                emergency_access.status != EMERGENCY_ACCESS_STATUS_RECOVERY_APPROVED:
            raise EmergencyAccessDoesNotExistException
        grantor = emergency_access.grantor
        result = {
            "obj": "emergencyAccessTakeover",
            "key_encrypted": emergency_access.key_encrypted,
            "kdf": grantor.kdf,
            "kdf_iterations": grantor.kdf_iterations
        }
        return result

    def password_emergency_access(self, emergency_access: EmergencyAccess, key: str, new_master_password_hash: str):
        if emergency_access.emergency_access_type != EMERGENCY_ACCESS_TYPE_TAKEOVER or \
                emergency_access.status != EMERGENCY_ACCESS_STATUS_RECOVERY_APPROVED:
            raise EmergencyAccessDoesNotExistException
        grantor = emergency_access.grantor
        self.user_repository.change_master_password(
            user=grantor, new_master_password_hash=new_master_password_hash, key=key
        )
        self.user_repository.revoke_all_sessions(user=grantor)
        # Remove grantor from all teams unless user is owner
        self.team_member_repository.leave_all_teams(
            user_id=grantor.user_id,
            status=PM_MEMBER_STATUS_CONFIRMED, personal_share=False,
            exclude_roles=[MEMBER_ROLE_OWNER]
        )
        mail_user_ids = self.notification_setting_repository.get_user_mail(
            category_id=NOTIFY_CHANGE_MASTER_PASSWORD, user_ids=[grantor.user_id]
        )
        return {
            "mail_user_ids": mail_user_ids,
            "grantor_user_id": grantor.user_id,
        }

    def id_password_emergency_access(self, emergency_access: EmergencyAccess):
        if emergency_access.emergency_access_type != EMERGENCY_ACCESS_TYPE_TAKEOVER or \
                emergency_access.status != EMERGENCY_ACCESS_STATUS_RECOVERY_APPROVED:
            raise EmergencyAccessDoesNotExistException
        grantor = emergency_access.grantor
        self.user_repository.revoke_all_sessions(user=grantor)
        mail_user_ids = self.notification_setting_repository.get_user_mail(
            category_id=NOTIFY_CHANGE_MASTER_PASSWORD, user_ids=[grantor.user_id]
        )
        return {
            "mail_user_ids": mail_user_ids,
            "grantor_user_id": grantor.user_id,
        }
