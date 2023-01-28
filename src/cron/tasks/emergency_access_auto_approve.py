import time
import schedule

from django.db import close_old_connections
from django.db.models import F

from cron.task import Task
from cystack_models.models.emergency_access.emergency_access import EmergencyAccess
from shared.utils.app import now
from shared.constants.emergency_access import *


class EmergencyAccessAutoApprove(Task):
    def __init__(self):
        super(EmergencyAccessAutoApprove, self).__init__()
        self.job_id = 'emergency_access_auto_approve'

    def register_job(self):
        pass

    def log_job_execution(self, run_time: float, exception: str = None, tb: str = None):
        pass

    def real_run(self, *args):
        # Close old connections
        close_old_connections()

        current_time = now()
        EmergencyAccess.objects.filter(
            status=EMERGENCY_ACCESS_STATUS_RECOVERY_INITIATED,
            recovery_initiated_date__lte=current_time - F('wait_time_days') * 86400
        ).update(status=EMERGENCY_ACCESS_STATUS_RECOVERY_APPROVED)

    def scheduling(self):
        schedule.every(20).minutes.do(self.run)
        while True:
            schedule.run_pending()
            time.sleep(1)
