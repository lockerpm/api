import time
import schedule

from django.conf import settings
from django.db import close_old_connections
from locker_server.containers.containers import cron_task_service
from locker_server.cron.task import Task


class ExpiringPlanNotification(Task):
    def __init__(self):
        super(ExpiringPlanNotification, self).__init__()
        self.job_id = 'expiring_plan_notification'

    def register_job(self):
        pass

    def log_job_execution(self, run_time: float, exception: str = None, tb: str = None):
        pass

    def real_run(self, *args):
        # Close old connections
        close_old_connections()

        try:
            self.pm_expiring_notify()
        except Exception as e:
            self.logger.error()
        # Close old connections
        close_old_connections()
        self.pm_enterprise_reminder()

    @staticmethod
    def pm_expiring_notify():
        cron_task_service.pm_expiring_notify(scope=settings.SCOPE_PWD_MANAGER)

    @staticmethod
    def pm_enterprise_reminder():
        cron_task_service.pm_enterprise_reminder()

    def scheduling(self):
        schedule.every().day.at("19:30").do(self.run)
        while True:
            schedule.run_pending()
            time.sleep(1)
