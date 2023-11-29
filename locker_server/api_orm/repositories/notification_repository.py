from typing import List, Optional

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_notification_model
from locker_server.core.entities.notification.notification import Notification
from locker_server.core.repositories.notification_repository import NotificationRepository
from locker_server.shared.utils.app import now

NotificationORM = get_notification_model()
ModelParser = get_model_parser()


class NotificationORMRepository(NotificationRepository):
    # ------------------------ List Notification resource ------------------- #
    def list_notifications(self, **filters) -> List[Notification]:
        user_id_param = filters.get("user_id")
        read_param = filters.get("read")
        scope_param = filters.get("scope")
        if user_id_param:
            notifications_orm = NotificationORM.objects.filter(user_id=user_id_param)
        else:
            notifications_orm = NotificationORM.objects.all()
        if read_param is not None:
            if read_param == "1" or read_param is True:
                notifications_orm = notifications_orm.filter(read=True)
            elif read_param == "0" or read_param is False:
                notifications_orm = notifications_orm.filter(read=False)
        if scope_param:
            notifications_orm = notifications_orm.filter(scope=scope_param)
        notifications_orm = notifications_orm.order_by("-publish_time")
        return [
            ModelParser.notification_parser().parse_notification(notification_orm=notification_orm)
            for notification_orm in notifications_orm
        ]

    def count_notifications(self, **filters) -> int:
        user_id_param = filters.get("user_id")
        read_param = filters.get("read")
        scope_param = filters.get("scope")
        if user_id_param:
            notifications_orm = NotificationORM.objects.filter(user_id=user_id_param).order_by('-publish_time')
        else:
            notifications_orm = NotificationORM.objects.all().order_by('-publish_time')
        if read_param is not None:
            if read_param == "1" or read_param is True:
                notifications_orm = notifications_orm.filter(read=True)
            elif read_param == "0" or read_param is False:
                notifications_orm = notifications_orm.filter(read=False)
        if scope_param:
            notifications_orm = notifications_orm.filter(scope=scope_param)
        return notifications_orm.count()

    # ------------------------ Get Notification resource --------------------- #
    def get_notification_by_id(self, notification_id: str) -> Optional[Notification]:
        try:
            notification_orm = NotificationORM.objects.get(id=notification_id)
        except NotificationORM.DoesNotExist:
            return None
        return ModelParser.notification_parser().parse_notification(notification_orm=notification_orm)

    # ------------------------ Create Notification resource --------------------- #
    def create_multiple(self, user_ids: [int], notification_type,
                        vi_title="", en_title="", vi_description="", en_description="", metadata=None):
        NotificationORM.create_multiple(
            user_ids=user_ids,
            notification_type=notification_type,
            vi_title=vi_title,
            en_title=en_title,
            vi_description=vi_description,
            en_description=en_description,
            metadata=metadata
        )

    # ------------------------ Update Notification resource --------------------- #
    def update_notification(self, notification_id: str, read: bool, clicked=None) -> Optional[Notification]:
        try:
            notification_orm = NotificationORM.objects.get(id=notification_id)
        except NotificationORM.DoesNotExist:
            return None
        notification_orm.read = read
        if read is True:
            notification_orm.read_time = now()
        else:
            notification_orm.read_time = None
        if clicked is not None:
            notification_metadata = notification_orm.get_metadata()
            notification_metadata["clicked"] = clicked
            notification_orm.metadata = notification_metadata
        notification_orm.save()
        return ModelParser.notification_parser().parse_notification(notification_orm=notification_orm)

    def read_all(self, **filters):
        user_id_param = filters.get("user_id")
        read_param = filters.get("read")
        scope_param = filters.get("scope")

        if user_id_param:
            notifications_orm = NotificationORM.objects.filter(user_id=user_id_param)
        else:
            notifications_orm = NotificationORM.objects.all()
        if read_param is not None:
            if read_param == "1" or read_param is True:
                notifications_orm = notifications_orm.filter(read=True)
            elif read_param == "0" or read_param is False:
                notifications_orm = notifications_orm.filter(read=False)
        if scope_param:
            notifications_orm = notifications_orm.filter(scope=scope_param)
        notifications_orm.update(read=True, read_time=now())

    # ------------------------ Delete Notification resource --------------------- #
