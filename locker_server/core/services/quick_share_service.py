from typing import Optional, Tuple

from locker_server.core.entities.quick_share.quick_share import QuickShare
from locker_server.core.exceptions.quick_share_exception import QuickShareDoesNotExistException, \
    QuickShareNotValidAccessException, QuickShareRequireOTPException
from locker_server.core.repositories.cipher_repository import CipherRepository
from locker_server.core.repositories.enterprise_repository import EnterpriseRepository
from locker_server.core.repositories.quick_share_repository import QuickShareRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.constants.ciphers import MAP_CIPHER_TYPE_STR
from locker_server.shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED
from locker_server.shared.constants.event import EVENT_ITEM_QUICK_SHARE_CREATED
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_EVENT
from locker_server.shared.external_services.pm_sync import PwdSync, SYNC_QUICK_SHARE
from locker_server.shared.utils.app import now


class QuickShareService:
    """
    This class represents Use Cases related QuickShare
    """
    def __init__(self,
                 quick_share_repository: QuickShareRepository,
                 cipher_repository: CipherRepository,
                 user_repository: UserRepository,
                 enterprise_repository: EnterpriseRepository):
        self.quick_share_repository = quick_share_repository
        self.cipher_repository = cipher_repository
        self.user_repository = user_repository
        self.enterprise_repository = enterprise_repository

    def get_by_id(self, quick_share_id: str) -> Optional[QuickShare]:
        quick_share = self.quick_share_repository.get_by_id(quick_share_id=quick_share_id)
        if not quick_share:
            raise QuickShareDoesNotExistException
        return quick_share

    def get_by_access_id(self, access_id: str) -> Optional[QuickShare]:
        quick_share = self.quick_share_repository.get_by_access_id(access_id=access_id)
        if not quick_share:
            raise QuickShareDoesNotExistException
        return quick_share

    def list_user_quick_shares(self, user_id: int):
        cipher_ids = self.cipher_repository.get_cipher_ids_created_by_user(user_id=user_id)
        quick_shares = self.quick_share_repository.list_quick_shares(**{
            "cipher_ids": cipher_ids
        })
        return quick_shares

    def create_user_quick_share(self, user_id: int, ip=None, **quick_share_data):
        quick_share = self.quick_share_repository.create_quick_share(**quick_share_data)
        self.user_repository.delete_sync_cache_data(user_id=user_id)
        PwdSync(event=SYNC_QUICK_SHARE, user_ids=[user_id]).send(
            data={"id": str(quick_share.quick_share_id)}
        )
        # Update activity logs:
        user_enterprise_ids = self.enterprise_repository.list_user_enterprise_ids(user_id=user_id, **{
            "status": E_MEMBER_STATUS_CONFIRMED
        })
        if user_enterprise_ids:
            cipher_id = quick_share_data.get("cipher_id")
            emails = [m.get("email") for m in quick_share_data.get("emails")]
            item_type = MAP_CIPHER_TYPE_STR.get(quick_share.cipher.cipher_type)
            BackgroundFactory.get_background(bg_name=BG_EVENT).run(func_name="create_by_enterprise_ids", **{
                "enterprise_ids": user_enterprise_ids, "user_id": user_id, "acting_user_id": user_id,
                "type": EVENT_ITEM_QUICK_SHARE_CREATED, "ip_address": ip, "cipher_id": cipher_id,
                "metadata": {"item_type": item_type, "emails": emails}
            })

        return quick_share

    def update_user_quick_share(self, quick_share: QuickShare, **quick_share_data):
        quick_share = self.quick_share_repository.update_quick_share(
            quick_share_id=quick_share.quick_share_id, **quick_share_data
        )
        if not quick_share:
            raise QuickShareDoesNotExistException
        return quick_share

    def delete_user_quick_share(self, user_id: int, quick_share: QuickShare):
        self.quick_share_repository.delete_quick_share(quick_share_id=quick_share.quick_share_id)
        self.user_repository.delete_sync_cache_data(user_id=user_id)
        PwdSync(event=SYNC_QUICK_SHARE, user_ids=[user_id]).send(
            data={"id": str(quick_share.quick_share_id)}
        )

    def public_quick_share(self, quick_share: QuickShare,
                           email: str = None, code: str = None, token: str = None) -> Tuple:
        if not self.quick_share_repository.check_valid_access(
            quick_share=quick_share, email=email, code=code, token=token
        ):
            raise QuickShareNotValidAccessException
        quick_share = self.quick_share_repository.update_access_count(
            quick_share_id=quick_share.quick_share_id, email=email
        )

        token = None
        expired_time = None
        if email and code and quick_share.is_public is False:
            token, expired_time = self.quick_share_repository.generate_public_access_token(
                quick_share=quick_share, email=email
            )
        if quick_share.cipher.created_by:
            self.user_repository.delete_sync_cache_data(user_id=quick_share.cipher.created_by.user_id)
        PwdSync(event=SYNC_QUICK_SHARE, user_ids=[quick_share.cipher.created_by.user_id]).send(
            data={"id": str(quick_share.quick_share_id)}
        )

        return quick_share, token, expired_time

    def check_access(self, quick_share: QuickShare, email: str) -> bool:
        return self.quick_share_repository.check_email_access(quick_share=quick_share, email=email)

    def get_email_access(self, quick_share: QuickShare) -> QuickShare:
        if quick_share.max_access_count and quick_share.access_count >= quick_share.max_access_count:
            raise QuickShareNotValidAccessException
        if quick_share.expiration_date and quick_share.expiration_date < now():
            raise QuickShareNotValidAccessException
        if quick_share.is_public is False:
            raise QuickShareRequireOTPException

        # Return data - Update access count
        quick_share = self.quick_share_repository.update_access_count(quick_share_id=quick_share.quick_share_id)
        self.user_repository.delete_sync_cache_data(user_id=quick_share.cipher.created_by.user_id)
        PwdSync(event=SYNC_QUICK_SHARE, user_ids=[quick_share.cipher.created_by.user_id]).send(
            data={"id": str(quick_share.quick_share_id)}
        )
        return quick_share

    def set_email_otp(self, quick_share: QuickShare, email: str) -> QuickShare:
        code = self.quick_share_repository.set_email_otp(quick_share_id=quick_share.quick_share_id, email=email)
        if not code:
            raise QuickShareDoesNotExistException
        return code
