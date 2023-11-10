from typing import Optional, List, NoReturn
from abc import ABC, abstractmethod

from locker_server.core.entities.notification.notification_setting import NotificationSetting


class NotificationSettingRepository(ABC):
    # ------------------------ List NotificationSetting resource ------------------- #
    @abstractmethod
    def list_user_notification_settings(self, user_id: int, **filters) -> List[NotificationSetting]:
        pass

    @abstractmethod
    def check_user_notification_settings(self, user_id: int) -> bool:
        pass

    # ------------------------ Get NotificationSetting resource --------------------- #
    @abstractmethod
    def get_user_notification(self, category_id: str, user_ids: List[int], is_notify: bool = True) -> List[int]:
        pass

    @abstractmethod
    def get_user_mail(self, category_id: str, user_ids: List[int], is_notify: bool = True) -> List[int]:
        pass

    @abstractmethod
    def get_user_notification_by_category_id(self, user_id: int, category_id: str) -> Optional[NotificationSetting]:
        pass

    # ------------------------ Create NotificationSetting resource --------------------- #
    @abstractmethod
    def create_multiple_notification_setting(self, user_id: int, categories: List[str]) -> NoReturn:
        pass

    # ------------------------ Update NotificationSetting resource --------------------- #
    @abstractmethod
    def update_notification_setting(self, notification_setting_id: str, notification_update_data) \
            -> Optional[NotificationSetting]:
        pass
    # ------------------------ Delete NotificationSetting resource --------------------- #
