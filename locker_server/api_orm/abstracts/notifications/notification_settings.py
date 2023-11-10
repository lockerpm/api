from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.constants.user_notification import LIST_NOTIFY_CATEGORIES


class AbstractNotificationSettingORM(models.Model):
    user = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="notification_settings"
    )
    category = models.ForeignKey(
        locker_server_settings.LS_NOTIFICATION_CATEGORY_MODEL, on_delete=models.CASCADE,
        related_name="notification_settings"
    )
    notification = models.BooleanField(default=True)
    mail = models.BooleanField(default=True)

    class Meta:
        abstract = True
        unique_together = ('user', 'category')



    # @classmethod
    # def get_user_notification(cls, category_id: str, user_ids, is_notify=True):
    #     exist_user_notifications = cls.objects.filter(user_id__in=user_ids, category_id=category_id)
    #     # Get non-exist user notification settings => The default value is True
    #     non_exist_user_notifications = diff_list(
    #         user_ids, list(exist_user_notifications.values_list('user_id', flat=True))
    #     )
    #     # Get list user_ids turn on/off notification
    #     notifications = list(
    #         exist_user_notifications.filter(notification=is_notify).values_list('user_id', flat=True)
    #     )
    #     # If we get list turn on, the returned result is non_exist_user_notifications and turn_on_notification
    #     return list(set(non_exist_user_notifications + notifications)) if is_notify is True else notifications
    #
    # @classmethod
    # def get_user_mail(cls, category_id: str, user_ids, is_notify=True):
    #     exist_user_notifications = cls.objects.filter(user_id__in=user_ids, category_id=category_id)
    #     # Get non-exist user notifications => The default value is True
    #     non_exist_user_notifications = diff_list(
    #         user_ids, list(exist_user_notifications.values_list('user_id', flat=True))
    #     )
    #     # Get list user_ids turn on/off mail
    #     mails = list(
    #         exist_user_notifications.filter(mail=is_notify).values_list('user_id', flat=True)
    #     )
    #
    #     # If we get list mail turn on, the returned result is non_exist_user_notifications and mail on
    #     return non_exist_user_notifications + mails if is_notify is True else mails
    #
    # def on_off_notification(self, turn_on: bool):
    #     self.notification = turn_on
    #     self.save()
    #
    # def on_off_mail(self, turn_on: bool):
    #     self.mail = turn_on
    #     self.save()
