from django.core.management import BaseCommand

from core.settings import CORE_CONFIG
from cystack_models.models import *


class Command(BaseCommand):
    cipher_repository = CORE_CONFIG["repositories"]["ICipherRepository"]()

    def handle(self, *args, **options):
        self.migrate_default_timeout()

    @staticmethod
    def migrate_default_timeout():
        User.objects.filter(timeout=15).update(timeout=20160)
