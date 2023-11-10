import time
import schedule

from django.conf import settings
from django.db import close_old_connections

from locker_server.containers.containers import cron_task_service
from locker_server.cron.task import Task


class EnterpriseMemberChangeBilling(Task):
    def __init__(self):
        super(EnterpriseMemberChangeBilling, self).__init__()
        self.job_id = 'enterprise_member_change_billing'

    def register_job(self):
        pass

    def log_job_execution(self, run_time: float, exception: str = None, tb: str = None):
        pass

    def real_run(self, *args):
        # Close old connections
        close_old_connections()
        cron_task_service.change_billing_enterprise_member(scope=settings.SCOPE_PWD_MANAGER)

    def scheduling(self):
        schedule.every().day.at("09:30").do(self.run)
        while True:
            schedule.run_pending()
            time.sleep(1)
