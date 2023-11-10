import time
import schedule

from django.db import close_old_connections

from locker_server.containers.containers import cron_task_service
from locker_server.cron.task import Task


class EnterpriseBreachScan(Task):
    def __init__(self):
        super(EnterpriseBreachScan, self).__init__()
        self.job_id = 'enterprise_breach_scan'

    def register_job(self):
        pass

    def log_job_execution(self, run_time: float, exception: str = None, tb: str = None):
        pass

    def real_run(self, *args):
        # Close old connections
        close_old_connections()

        cron_task_service.breach_scan()

    def scheduling(self):
        schedule.every().day.at("19:00").do(self.run)
        while True:
            schedule.run_pending()
            time.sleep(1)
