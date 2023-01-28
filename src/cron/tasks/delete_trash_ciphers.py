import time
import schedule

from django.db import close_old_connections

from cron.task import Task
from cystack_models.models.ciphers.ciphers import Cipher
from shared.utils.app import now


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
        Cipher.objects.filter(deleted_date__isnull=False).filter(deleted_date__lte=current_time - 30 * 86400).delete()

    def scheduling(self):
        schedule.every().day.at("17:00").do(self.run)
        while True:
            schedule.run_pending()
            time.sleep(1)
