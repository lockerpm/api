from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from locker_server.core.entities.quick_share.quick_share import QuickShare
from locker_server.core.entities.release.release import Release


class QuickShareRepository(ABC):

    # ------------------------ List QuickShare resource ------------------- #
    @abstractmethod
    def list_quick_shares(self, parse_emails=True, **filter_params) -> List[QuickShare]:
        pass

    # ------------------------ Get QuickShare resource --------------------- #
    @abstractmethod
    def get_by_id(self, quick_share_id: str) -> Optional[QuickShare]:
        pass

    @abstractmethod
    def get_by_access_id(self, access_id: str, parse_emails=True) -> Optional[QuickShare]:
        pass

    @abstractmethod
    def check_valid_access(self, quick_share: QuickShare, email: str = None, code: str = None,
                           token: str = None) -> bool:
        pass

    @abstractmethod
    def check_email_access(self, quick_share: QuickShare, email: str = None) -> bool:
        pass

    # ------------------------ Create QuickShare resource --------------------- #
    @abstractmethod
    def create_quick_share(self, **quick_share_data) -> QuickShare:
        pass

    @abstractmethod
    def generate_public_access_token(self, quick_share: QuickShare, email: str) -> Tuple:
        pass

    # ------------------------ Update QuickShare resource --------------------- #
    @abstractmethod
    def update_quick_share(self, quick_share_id: str, **quick_share_data) -> Optional[QuickShare]:
        pass

    @abstractmethod
    def update_access_count(self, quick_share_id: str, amount: int = 1, email: str = None) -> Optional[QuickShare]:
        pass

    @abstractmethod
    def set_email_otp(self, quick_share_id: str, email: str) -> Optional[str]:
        pass

    # ------------------------ Delete QuickShare resource --------------------- #
    @abstractmethod
    def delete_quick_share(self, quick_share_id: str):
        pass
