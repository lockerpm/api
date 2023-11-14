from django.core.management import BaseCommand

from locker_server.api_orm.models import *
from locker_server.api_orm.models.wrapper import *


class Command(BaseCommand):
    def handle(self, *args, **options):
        users = get_user_model().objects.count()
        enterprises = get_enterprise_model().objects.count()
        first_enterprise = get_enterprise_model().objects.first()
        members = first_enterprise.enterprise_members.count()
        print("Count:::", users)
        print("Enterprise:::", enterprises, members)
