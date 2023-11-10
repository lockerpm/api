from locker_server.api_orm.abstracts.notifications.notification_category import AbstractNotificationCategoryORM


class NotificationCategoryORM(AbstractNotificationCategoryORM):
    class Meta(AbstractNotificationCategoryORM.Meta):
        swappable = 'LS_NOTIFICATION_CATEGORY_MODEL'
        db_table = 'cs_notification_categories'
