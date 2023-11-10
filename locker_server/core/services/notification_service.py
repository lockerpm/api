from typing import List, Optional

from locker_server.core.entities.notification.notification import Notification
from locker_server.core.exceptions.notification_exception import NotificationDoesNotExistException
from locker_server.core.repositories.notification_repository import NotificationRepository
from locker_server.core.repositories.user_repository import UserRepository


class NotificationService:
    """
    This class represents Use Cases related User
    """

    def __init__(self, notification_repository: NotificationRepository,
                 user_repository: UserRepository,
                 ):
        self.user_repository = user_repository
        self.notification_repository = notification_repository

    def list_notifications(self, **filters) -> List[Notification]:
        return self.notification_repository.list_notifications(**filters)

    def count_notifications(self, **filters) -> int:
        return self.notification_repository.count_notifications(**filters)

    def get_notification_by_id(self, notification_id: str) -> Optional[Notification]:
        notification = self.notification_repository.get_notification_by_id(
            notification_id=notification_id
        )
        if not notification:
            raise NotificationDoesNotExistException
        return notification

    def update_notification(self, notification_id: str, read: bool, clicked=None):
        updated_notification = self.notification_repository.update_notification(
            notification_id=notification_id,
            read=read,
            clicked=clicked
        )
        if not updated_notification:
            raise NotificationDoesNotExistException
        return updated_notification

    def read_all(self, **filters):
        self.notification_repository.read_all(**filters)

    def create_multiple(self, user_ids: [int], notification_type,
                        vi_title="", en_title="", vi_description="", en_description="", metadata=None):
        self.notification_repository.create_multiple(
            user_ids=user_ids,
            notification_type=notification_type,
            vi_title=vi_title,
            en_title=en_title,
            vi_description=vi_description,
            en_description=en_description,
            metadata=metadata
        )
