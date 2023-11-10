import os
import time
import schedule

from django.conf import settings
from django.db import close_old_connections

from locker_server.containers.containers import cron_task_service
from locker_server.cron.task import Task


class Feedback(Task):
    def __init__(self):
        super(Feedback, self).__init__()
        self.job_id = 'feedback'

    def register_job(self):
        pass

    def log_job_execution(self, run_time: float, exception: str = None, tb: str = None):
        pass

    def real_run(self, *args):
        # Close old connections
        close_old_connections()
        try:
            self.log_new_users()
        except Exception as e:
            self.logger.error()

        try:
            self.asking_for_feedback_after_subscription()
        except Exception as e:
            self.logger.error()

    def log_new_users(self):
        cron_task_service.log_new_users()

    def asking_for_feedback_after_subscription(self):
        cron_task_service.asking_for_feedback_after_subscription(scope=settings.SCOPE_PWD_MANAGER)

    def scheduling(self):
        if os.getenv("PROD_ENV") != "staging":
            schedule.every().day.at("10:00").do(self.run)
            while True:
                schedule.run_pending()
                time.sleep(1)
