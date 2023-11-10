from django.core.management import BaseCommand

from locker_server.api_orm.models.wrapper import *
from locker_server.containers.containers import user_service
from locker_server.shared.constants.transactions import PLAN_TYPE_PM_FREE, PLAN_TYPE_PM_PREMIUM
from locker_server.shared.utils.app import now


class Command(BaseCommand):
    def handle(self, *args, **options):
        user_plan_model = get_user_plan_model()
        user_plan_frees_orm = user_plan_model.objects.filter(
            pm_plan__alias=PLAN_TYPE_PM_FREE
        )
        for user_plan_free_orm in user_plan_frees_orm:
            start_period = user_plan_free_orm.start_period
            if start_period is None:
                start_period = now()
            end_period = locker_server_settings.DEFAULT_PLAN_TIME + start_period
            user_service.update_plan(
                user_id=user_plan_free_orm.user_id, plan_type_alias=PLAN_TYPE_PM_PREMIUM,
                duration=user_plan_free_orm.duration,
                **{
                    "start_period": start_period,
                    "end_period": end_period
                }
            )
        print("Success")
