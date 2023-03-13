from django.core.management import BaseCommand

from core.settings import CORE_CONFIG
from cystack_models.models import *


class Command(BaseCommand):
    cipher_repository = CORE_CONFIG["repositories"]["ICipherRepository"]()

    def handle(self, *args, **options):
        from shared.background import BG_NOTIFY
        from shared.background import LockerBackgroundFactory
        from django.conf import settings
        user = User.objects.get(user_id=802)
        LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="notify_locker_mail", **{
                "user_ids": [user.user_id],
                "job": "upgraded_to_lifetime_from_code",
                "scope": settings.SCOPE_PWD_MANAGER,
                "service_name": user.saas_source,
            }
        )
