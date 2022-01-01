from django.core.management import BaseCommand

from core.settings import CORE_CONFIG
from cystack_models.models import *


class Command(BaseCommand):
    def handle(self, *args, **options):
        team_repository = CORE_CONFIG["repositories"]["ITeamRepository"]()
        ciphers = Cipher.objects.all()
        for cipher in ciphers:
            if cipher.user:
                cipher.created_by = cipher.user
                cipher.save()
            elif cipher.team:
                cipher.created_by = team_repository.get_primary_member(team=cipher.team).user
                cipher.save()
            print("Done cipher {}".format(cipher.id))
