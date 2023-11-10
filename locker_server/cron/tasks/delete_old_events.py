import time
import schedule

from django.db import close_old_connections

from locker_server.containers.containers import cron_task_service
from locker_server.cron.task import Task
from locker_server.shared.utils.app import now


class DeleteOldEvents(Task):
    def __init__(self):
        super(DeleteOldEvents, self).__init__()
        self.job_id = 'delete_old_events'

    def register_job(self):
        pass

    def log_job_execution(self, run_time: float, exception: str = None, tb: str = None):
        pass

    def real_run(self, *args):
        # Close old connections
        close_old_connections()
        current_time = now()
        creation_date_pivot = current_time - 90 * 86400
        # Delete old events if the creation date is less than 90 days
        cron_task_service.delete_old_events(creation_date_pivot=creation_date_pivot)

    def scheduling(self):
        schedule.every().day.at("17:00").do(self.run)
        while True:
            schedule.run_pending()
            time.sleep(1)
