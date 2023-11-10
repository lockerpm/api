from typing import List, Optional

from locker_server.core.entities.notification.notification_setting import NotificationSetting
from locker_server.core.exceptions.notification_setting_exception import NotificationSettingDoesNotExistException
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.core.repositories.notification_setting_repository import NotificationSettingRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.shared.constants.user_notification import LIST_NOTIFY_CATEGORIES


class NotificationSettingService:
    """
    This class represents Use Cases related notification setting
    """

    def __init__(self, notification_setting_repository: NotificationSettingRepository, user_repository: UserRepository):
        self.notification_setting_repository = notification_setting_repository
        self.user_repository = user_repository

    def list_user_notification_settings(self, user_id: int, **filters) -> List[NotificationSetting]:
        user = self.user_repository.get_user_by_id(user_id=user_id)
        if not user:
            raise UserDoesNotExistException
        notification_settings_existed = self.notification_setting_repository.check_user_notification_settings(
            user_id=user_id
        )
        if not notification_settings_existed:
            self.notification_setting_repository.create_multiple_notification_setting(
                user_id=user_id,
                categories=LIST_NOTIFY_CATEGORIES
            )
        notification_settings = self.notification_setting_repository.list_user_notification_settings(
            user_id=user_id,
            **filters
        )
        return notification_settings

    def get_notification_setting_by_category_id(self, user_id: int, category_id: str) -> Optional[NotificationSetting]:
        notification_setting = self.notification_setting_repository.get_user_notification_by_category_id(
            user_id=user_id,
            category_id=category_id
        )
        if not notification_setting:
            raise NotificationSettingDoesNotExistException
        return notification_setting

    def update_notification_setting(self, notification_setting_id: str, notification_update_data) \
            -> Optional[NotificationSetting]:
        notification_setting = self.notification_setting_repository.update_notification_setting(
            notification_setting_id=notification_setting_id,
            notification_update_data=notification_update_data
        )
        if not notification_setting:
            raise NotificationSettingDoesNotExistException
        return notification_setting
