from locker_server.api_orm.abstracts.notifications.notification_settings import AbstractNotificationSettingORM
from locker_server.shared.constants.user_notification import LIST_NOTIFY_CATEGORIES


class NotificationSettingORM(AbstractNotificationSettingORM):
    class Meta(AbstractNotificationSettingORM.Meta):
        swappable = 'LS_NOTIFICATION_SETTING_MODEL'
        db_table = 'cs_notification_settings'

    @classmethod
    def create_default_multiple(cls, user_id: int, categories=LIST_NOTIFY_CATEGORIES):
        profile_notifications = [
            cls(category_id=category_id, user_id=user_id) for category_id in categories
        ]
        cls.objects.bulk_create(profile_notifications, ignore_conflicts=True)
