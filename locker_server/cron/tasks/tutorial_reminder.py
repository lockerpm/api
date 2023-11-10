import os
import time
import schedule

from django.db import close_old_connections

from locker_server.containers.containers import cron_task_service
from locker_server.cron.task import Task


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
        duration_unit = 86400  # day
        if os.getenv("PROD_ENV") == "staging":
            duration_unit = 15 * 60  # 15 minutes
        cron_task_service.tutorial_reminder(duration_unit=duration_unit)

    def scheduling(self):
        # TODO: Test on staging
        if os.getenv("PROD_ENV") == "staging":
            schedule.every(15).minutes.do(self.run)
            while True:
                schedule.run_pending()
                time.sleep(1)
