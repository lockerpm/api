from typing import Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.notification.notification_category import NotificationCategory


class NotificationCategoryRepository(ABC):
    # ------------------------ List NotificationCategory resource ------------------- #
    @abstractmethod
    def list_notification_categories(self) -> List[NotificationCategory]:
        pass

    # ------------------------ Get NotificationCategory resource --------------------- #
    @abstractmethod
    def get_by_id(self, notification_category_id: str) -> Optional[NotificationCategory]:
        pass

    # ------------------------ Create NotificationCategory resource --------------------- #

    # ------------------------ Update NotificationCategory resource --------------------- #

    # ------------------------ Delete NotificationCategory resource --------------------- #
