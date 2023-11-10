import time
import schedule

from django.db import close_old_connections

from locker_server.containers.containers import cron_task_service
from locker_server.cron.task import Task
from locker_server.shared.utils.app import now


class DeleteTrashCiphers(Task):
    def __init__(self):
        super(DeleteTrashCiphers, self).__init__()
        self.job_id = 'delete_trash_ciphers'

    def register_job(self):
        pass

    def log_job_execution(self, run_time: float, exception: str = None, tb: str = None):
        pass

    def real_run(self, *args):
        # Close old connections
        close_old_connections()
        current_time = now()
        # Delete ciphers in trash if the deleted time is less than 30 days
        deleted_date_pivot = current_time - 30 * 86400
        cron_task_service.delete_trash_ciphers(deleted_date_pivot=deleted_date_pivot)

    def scheduling(self):
        schedule.every().day.at("17:00").do(self.run)
        while True:
            schedule.run_pending()
            time.sleep(1)
