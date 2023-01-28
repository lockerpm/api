import time
import schedule

from django.conf import settings
from django.db import close_old_connections
from django.db.models import Count, F

from cron.task import Task
from core.settings import CORE_CONFIG
from cystack_models.models.user_plans.pm_user_plan import PMUserPlan
from shared.background import LockerBackgroundFactory, BG_NOTIFY
from shared.constants.transactions import *
from shared.utils.app import now


class DowngradePlan(Task):
    def __init__(self):
        super(DowngradePlan, self).__init__()
        self.job_id = 'downgrade_plan'

    def register_job(self):
        pass

    def log_job_execution(self, run_time: float, exception: str = None, tb: str = None):
        pass

    def real_run(self, *args):
        # Close old connections
        close_old_connections()

        user_repository = CORE_CONFIG["repositories"]["IUserRepository"]()
        pm_user_plans = PMUserPlan.objects.filter(pm_stripe_subscription__isnull=True).exclude(
            pm_plan__alias=PLAN_TYPE_PM_FREE
        ).exclude(end_period__isnull=True).filter(end_period__lte=now()).annotate(
            family_members_count=Count('user__pm_plan_family')
        ).filter(family_members_count__lt=1)
        for pm_user_plan in pm_user_plans:
            user = pm_user_plan.user
            pm_plan = pm_user_plan.get_plan_obj()
            current_plan_name = pm_plan.get_name()

            # If user cancels at the end of period => Downgrade
            if pm_user_plan.cancel_at_period_end is True:
                user_repository.update_plan(
                    user=user, plan_type_alias=PLAN_TYPE_PM_FREE, scope=settings.SCOPE_PWD_MANAGER
                )
                LockerBackgroundFactory.get_background(
                    bg_name=BG_NOTIFY, background=False
                ).run(func_name="downgrade_plan", **{
                    "user_id": user.user_id, "old_plan": current_plan_name, "downgrade_time": now(),
                    "scope": settings.SCOPE_PWD_MANAGER
                })
                continue

            # If the subscription by mobile app => Continue
            if pm_user_plan.default_payment_method in [PAYMENT_METHOD_MOBILE]:
                continue

            # Else, check the attempts number
            # Attempts only apply for the Enterprise plan
            if pm_user_plan.pm_plan.is_team_plan and pm_user_plan.attempts < MAX_ATTEMPTS:
                pm_user_plan.end_period = PMUserPlan.get_next_attempts_duration(
                    current_number_attempts=pm_user_plan.attempts
                ) + now()
                pm_user_plan.attempts = F('attempts') + 1
                pm_user_plan.save()
                pm_user_plan.refresh_from_db()
                # Notify for user here
                LockerBackgroundFactory.get_background(
                    bg_name=BG_NOTIFY, background=False
                ).run(func_name="pay_failed", **{
                    "user_id": user.user_id,
                    "current_attempt": pm_user_plan.attempts,
                    "next_attempt": PMUserPlan.get_next_attempts_day_str(current_number_attempts=pm_user_plan.attempts),
                    "scope": settings.SCOPE_PWD_MANAGER
                })
            else:
                # Cancel the subscription of the user and notify for this user
                user_repository.update_plan(
                    user=user, plan_type_alias=PLAN_TYPE_PM_FREE, scope=settings.SCOPE_PWD_MANAGER
                )
                LockerBackgroundFactory.get_background(
                    bg_name=BG_NOTIFY, background=False
                ).run(func_name="downgrade_plan", **{
                    "user_id": user.user_id, "old_plan": current_plan_name, "downgrade_time": now(),
                    "scope": settings.SCOPE_PWD_MANAGER
                })

    def scheduling(self):
        schedule.every(10).minutes.do(self.run)
        while True:
            schedule.run_pending()
            time.sleep(1)
