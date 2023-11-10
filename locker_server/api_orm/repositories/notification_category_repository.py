from typing import List, Optional

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_notification_category_model
from locker_server.core.entities.notification.notification_category import NotificationCategory
from locker_server.core.repositories.notification_category_repository import NotificationCategoryRepository


NotificationCategoryORM = get_notification_category_model()
ModelParser = get_model_parser()


class NotificationCategoryORMRepository(NotificationCategoryRepository):
    # ------------------------ List NotificationCategory resource ------------------- #
    def list_notification_categories(self) -> List[NotificationCategory]:
        notification_categories_orm = NotificationCategoryORM.objects.all().order_by('order_number')
        return [
            ModelParser.notification_parser().parse_notification_category(
                notification_category_orm=notification_category_orm
            ) for notification_category_orm in notification_categories_orm
        ]

    # ------------------------ Get NotificationCategory resource --------------------- #
    def get_by_id(self, notification_category_id: str) -> Optional[NotificationCategory]:
        try:
            notification_category_orm = NotificationCategoryORM.objects.get(id=notification_category_id)
            return ModelParser.notification_parser().parse_notification_category(
                notification_category_orm=notification_category_orm
            )
        except NotificationCategoryORM.DoesNotExist:
            return None

    # ------------------------ Create NotificationCategory resource --------------------- #

    # ------------------------ Update NotificationCategory resource --------------------- #

    # ------------------------ Delete NotificationCategory resource --------------------- #
