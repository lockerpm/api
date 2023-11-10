from typing import Optional, List, NoReturn
from abc import ABC, abstractmethod

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_notification_setting_model
from locker_server.core.entities.notification.notification_setting import NotificationSetting
from locker_server.core.repositories.notification_setting_repository import NotificationSettingRepository
from locker_server.shared.utils.app import diff_list

NotificationSettingORM = get_notification_setting_model()
ModelParser = get_model_parser()


class NotificationSettingORMRepository(NotificationSettingRepository):
    # ------------------------ List NotificationSetting resource ------------------- #
    def list_user_notification_settings(self, user_id: int, **filters) -> List[NotificationSetting]:
        notification_settings_orm = NotificationSettingORM.objects.filter(
            user_id=user_id
        ).select_related("category").order_by('category__order_number')
        type_param = filters.get("type")
        if type_param:
            if type_param == "notification":
                notification_settings_orm = notification_settings_orm.filter(
                    category__notification=True
                )
            elif type_param == "mail":
                notification_settings_orm = notification_settings_orm.filter(
                    category__mail=True
                )
        return [
            ModelParser.notification_parser().parse_notification_settings(
                notification_setting_orm=notification_setting_orm
            )
            for notification_setting_orm in notification_settings_orm
        ]

    def check_user_notification_settings(self, user_id: int) -> bool:
        return NotificationSettingORM.objects.filter(user_id=user_id).exists()

    # ------------------------ Get NotificationSetting resource --------------------- #
    def get_user_notification(self, category_id: str, user_ids: List[int], is_notify: bool = True) -> List[int]:
        exist_user_notifications = NotificationSettingORM.objects.filter(user_id__in=user_ids, category_id=category_id)
        # Get non-exist user notification settings => The default value is True
        non_exist_user_notifications = diff_list(
            user_ids, list(exist_user_notifications.values_list('user_id', flat=True))
        )
        # Get list user_ids turn on/off notification
        notifications = list(
            exist_user_notifications.filter(notification=is_notify).values_list('user_id', flat=True)
        )
        # If we get list turn on, the returned result is non_exist_user_notifications and turn_on_notification
        return list(set(non_exist_user_notifications + notifications)) if is_notify is True else notifications

    def get_user_mail(self, category_id: str, user_ids: List[int], is_notify: bool = True) -> List[int]:
        exist_user_notifications = NotificationSettingORM.objects.filter(user_id__in=user_ids, category_id=category_id)
        # Get non-exist user notifications => The default value is True
        non_exist_user_notifications = diff_list(
            user_ids, list(exist_user_notifications.values_list('user_id', flat=True))
        )
        # Get list user_ids turn on/off mail
        mails = list(
            exist_user_notifications.filter(mail=is_notify).values_list('user_id', flat=True)
        )

        # If we get list mail turn on, the returned result is non_exist_user_notifications and mail on
        return non_exist_user_notifications + mails if is_notify is True else mails

    # ------------------------ Create NotificationSetting resource --------------------- #
    def create_multiple_notification_setting(self, user_id: int, categories: List[str]) -> NoReturn:
        NotificationSettingORM.create_default_multiple(
            user_id=user_id,
            categories=categories
        )

    def get_user_notification_by_category_id(self, user_id: int, category_id: str) -> Optional[NotificationSetting]:
        try:
            notification_setting_orm = NotificationSettingORM.objects.get(user_id=user_id, category_id=category_id)
        except NotificationSettingORM.DoesNotExist:
            return None
        return ModelParser.notification_parser().parse_notification_settings(
            notification_setting_orm=notification_setting_orm
        )

    # ------------------------ Update NotificationSetting resource --------------------- #
    def update_notification_setting(self, notification_setting_id: str, notification_update_data) \
            -> Optional[NotificationSetting]:
        try:
            notification_orm = NotificationSettingORM.objects.get(id=notification_setting_id)
        except NotificationSettingORM.DoesNotExist:
            return None
        notification_orm.notification = notification_update_data.get("notification", notification_orm.notification)
        notification_orm.mail = notification_update_data.get("mail", notification_orm.mail)
        notification_orm.save()
        return ModelParser.notification_parser().parse_notification_settings(
            notification_setting_orm=notification_orm
        )

        # ------------------------ Delete NotificationSetting resource --------------------- #
