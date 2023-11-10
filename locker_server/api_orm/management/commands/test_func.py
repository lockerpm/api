from django.core.management import BaseCommand

from locker_server.api_orm.models import *
from locker_server.api_orm.models.wrapper import *
from locker_server.shared.external_services.locker_background.background_factory import BackgroundFactory
from locker_server.shared.external_services.locker_background.constants import BG_NOTIFY
from locker_server.shared.external_services.user_notification.list_jobs import PWD_NEW_SHARE_ITEM
from locker_server.shared.external_services.user_notification.notification_sender import *
from locker_server.shared.utils.app import get_ip_location


class Command(BaseCommand):
    def handle(self, *args, **options):
        # ip = "222.252.28.231"
        # ip_location = get_ip_location(ip=ip)
        # print(ip_location)

        user_ids = [34]
        service = SENDING_SERVICE_WEB_NOTIFICATION
        # service = SENDING_SERVICE_MAIL
        BackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="notify_sending", **{
                "user_ids": user_ids,
                "services": [service],
                "job": PWD_NEW_SHARE_ITEM,
                "cipher_type": "1",
                "owner_name": "KHAI TQ Test",
            }
        )