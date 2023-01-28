import os
import time
import schedule

from django.db import close_old_connections
from django.db.models import F

from cron.task import Task
from cystack_models.models import User, EnterpriseMember
from shared.background import LockerBackgroundFactory, BG_NOTIFY
from shared.constants.enterprise_members import E_MEMBER_STATUS_CONFIRMED
from shared.utils.app import now


class TutorialReminder(Task):
    def __init__(self):
        super(TutorialReminder, self).__init__()
        self.job_id = 'tutorial_reminder'

    def register_job(self):
        pass

    def log_job_execution(self, run_time: float, exception: str = None, tb: str = None):
        pass

    def real_run(self, *args):
        # Close old connections
        close_old_connections()

        current_time = now()

        users = User.objects.filter()
        enterprise_user_ids = EnterpriseMember.objects.filter(
            status=E_MEMBER_STATUS_CONFIRMED
        ).values_list('user_id', flat=True)
        exclude_enterprise_users = users.exclude(user_id__in=enterprise_user_ids)

        duration_unit = 86400  # day
        if os.getenv("PROD_ENV") == "staging":
            duration_unit = 15 * 60  # 15 minutes

        # 3 days
        users_3days = users.filter(
            creation_date__range=(current_time - 3 * duration_unit, current_time - 2 * duration_unit)
        ).values_list('user_id', flat=True)
        LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="notify_tutorial", **{
                "job": "tutorial_day_3_add_items", "user_ids": list(users_3days),
            }
        )

        # 5 days
        users_5days = users.filter(
            creation_date__range=(current_time - 5 * duration_unit, current_time - 4 * duration_unit)
        ).values_list('user_id', flat=True)
        LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="notify_tutorial", **{
                "job": "tutorial_day_5_download", "user_ids": list(users_5days),
            }
        )

        # 7 days
        users_7days = users.filter(
            creation_date__range=(current_time - 7 * duration_unit, current_time - 6 * duration_unit)
        ).values_list('user_id', flat=True)
        LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="notify_tutorial", **{
                "job": "tutorial_day_7_autofill", "user_ids": list(users_7days),
            }
        )

        # 13 days
        users_13days = exclude_enterprise_users.exclude(
            pm_user_plan__start_period__isnull=True
        ).exclude(
            pm_user_plan__end_period__isnull=True
        ).annotate(
            plan_period=F('pm_user_plan__end_period') - F('pm_user_plan__start_period'),
            remain_period=F('pm_user_plan__end_period') - current_time
        ).filter(
            plan_period__lte=15 * duration_unit, remain_period__lte=duration_unit, remain_period__gte=0
        ).values_list('user_id', flat=True)
        LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="notify_tutorial", **{
                "job": "tutorial_day_13_trial_end", "user_ids": list(users_13days),
            }
        )

        # 20 days
        users_20days = exclude_enterprise_users.filter(
            creation_date__range=(current_time - 20 * duration_unit, current_time - 19 * duration_unit)
        ).values_list('user_id', flat=True)
        LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
            func_name="notify_tutorial", **{
                "job": "tutorial_day_20_refer_friend", "user_ids": list(users_20days),
            }
        )

    def scheduling(self):
        # TODO: Test on staging
        if os.getenv("PROD_ENV") == "staging":
            schedule.every(15).minutes.do(self.run)
            while True:
                schedule.run_pending()
                time.sleep(1)
