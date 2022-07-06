from django.db import models

from cystack_models.models.users.users import User
from cystack_models.models.notifications.notification_category import NotificationCategory
from shared.constants.user_notification import LIST_NOTIFY_CATEGORIES
from shared.utils.app import diff_list


class NotificationSetting(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notification_settings")
    category = models.ForeignKey(NotificationCategory, on_delete=models.CASCADE, related_name="notification_settings")
    notification = models.BooleanField(default=True)
    mail = models.BooleanField(default=True)

    class Meta:
        db_table = 'cs_notification_settings'
        unique_together = ('user', 'category')

    @classmethod
    def create_default_multiple(cls, user: User, categories=LIST_NOTIFY_CATEGORIES):
        profile_notifications = [
            cls(category_id=category_id, user=user) for category_id in categories
        ]
        cls.objects.bulk_create(profile_notifications, ignore_conflicts=True)

    @classmethod
    def get_user_notification(cls, category_id: str, user_ids, is_notify=True):
        exist_user_notifications = cls.objects.filter(user_id__in=user_ids, category_id=category_id)
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

    @classmethod
    def get_user_mail(cls, category_id: str, user_ids, is_notify=True):
        exist_user_notifications = cls.objects.filter(user_id__in=user_ids, category_id=category_id)
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

    def on_off_notification(self, turn_on: bool):
        self.notification = turn_on
        self.save()

    def on_off_mail(self, turn_on: bool):
        self.mail = turn_on
        self.save()
