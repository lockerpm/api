from locker_server.core.entities.notification.notification_category import NotificationCategory
from locker_server.core.entities.user.user import User


class NotificationSetting(object):
    def __init__(self, notification_setting_id: int, user: User, category: NotificationCategory,
                 notification: bool = True, mail: bool = True):
        self._notification_setting_id = notification_setting_id
        self._user = user
        self._category = category
        self._notification = notification
        self._mail = mail

    @property
    def notification_setting_id(self):
        return self._notification_setting_id

    @property
    def user(self):
        return self._user

    @property
    def category(self):
        return self._category

    @property
    def notification(self):
        return self._notification

    @property
    def mail(self):
        return self._mail
