from django.conf import settings
from django.core.management import BaseCommand

from core.settings import CORE_CONFIG
from cystack_models.models import *
from shared.constants.transactions import *
from shared.utils.app import now


class Command(BaseCommand):
    user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()

    def handle(self, *args, **options):

        user = User.objects.get(user_id=6403)
        plan_obj = PMPlan.objects.get(alias=PLAN_TYPE_PM_ENTERPRISE)
        enterprise_name = "My Enterprise"

        end_period = now() + 13 * 86400
        number_members = 1
        plan_metadata = {
            "start_period": now(),
            "end_period": end_period,
            "number_members": number_members,
            "enterprise_name": enterprise_name
        }
        self.user_repository.update_plan(
            user=user, plan_type_alias=plan_obj.get_alias(),
            duration=DURATION_MONTHLY, scope=settings.SCOPE_PWD_MANAGER, **plan_metadata
        )
        print("Done")