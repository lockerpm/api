from locker_server.api_orm.model_parsers.wrapper_specific_model_parser import get_specific_model_parser
from locker_server.api_orm.models import *
from locker_server.core.entities.notification.notification import Notification
from locker_server.core.entities.notification.notification_category import NotificationCategory
from locker_server.core.entities.notification.notification_setting import NotificationSetting


class NotificationParser:
    @classmethod
    def parse_notification_category(cls, notification_category_orm: NotificationCategoryORM) -> NotificationCategory:
        return NotificationCategory(
            notification_category_id=notification_category_orm.id,
            name=notification_category_orm.name,
            name_vi=notification_category_orm.name_vi,
            notification=notification_category_orm.notification,
            mail=notification_category_orm.mail,
            order_number=notification_category_orm.order_number
        )

    @classmethod
    def parse_notification_settings(cls, notification_setting_orm: NotificationSettingORM) -> NotificationSetting:
        user_parser = get_specific_model_parser("UserParser")
        return NotificationSetting(
            notification_setting_id=notification_setting_orm.id,
            user=user_parser.parse_user(user_orm=notification_setting_orm.user),
            category=cls.parse_notification_category(notification_category_orm=notification_setting_orm.category),
            notification=notification_setting_orm.notification,
            mail=notification_setting_orm.mail,
        )

    @classmethod
    def parse_notification(cls, notification_orm: NotificationORM) -> Notification:
        user_parser = get_specific_model_parser("UserParser")
        return Notification(
            notification_id=notification_orm.id,
            type=notification_orm.type,
            scope=notification_orm.scope,
            publish_time=notification_orm.publish_time,
            title=notification_orm.title,
            description=notification_orm.description,
            metadata=notification_orm.metadata,
            read=notification_orm.read,
            read_time=notification_orm.read_time,
            user=user_parser.parse_user(user_orm=notification_orm.user)
        )
