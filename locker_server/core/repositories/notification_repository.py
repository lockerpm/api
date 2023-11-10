from typing import Optional, List, NoReturn
from abc import ABC, abstractmethod

from locker_server.core.entities.notification.notification import Notification


class NotificationRepository(ABC):
    # ------------------------ List Notification resource ------------------- #
    @abstractmethod
    def list_notifications(self, **filters) -> List[Notification]:
        pass

    @abstractmethod
    def count_notifications(self, **filters) -> int:
        pass

    # ------------------------ Get Notification resource --------------------- #
    @abstractmethod
    def get_notification_by_id(self, notification_id: str) -> Optional[Notification]:
        pass

    # ------------------------ Create Notification resource --------------------- #
    @abstractmethod
    def create_multiple(self, user_ids: [int], notification_type,
                        vi_title="", en_title="", vi_description="", en_description="", metadata=None):
        pass

    # ------------------------ Update Notification resource --------------------- #
    @abstractmethod
    def update_notification(self, notification_id: str, read: bool, clicked=None) -> Optional[Notification]:
        pass

    @abstractmethod
    def read_all(self, **filters) -> NoReturn:
        pass
    # ------------------------ Delete Notification resource --------------------- #
