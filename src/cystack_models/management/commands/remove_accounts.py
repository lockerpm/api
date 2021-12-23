import json

import humps
import requests

from django.core.management import BaseCommand

from core.settings import CORE_CONFIG
from cystack_models.models import *


class Command(BaseCommand):
    def handle(self, *args, **options):
        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        users = User.objects.filter(user_id__in=[6037])
        for user in users:
            primary_team = user_repository.get_default_team(user=user)
            if primary_team:
                primary_team.delete()
        Cipher.objects.filter(user__in=users).delete()
        users.delete()

