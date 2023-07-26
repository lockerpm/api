import time
import schedule

from django.db import close_old_connections

from cron.task import Task
from cystack_models.models.enterprises.enterprises import Enterprise
from shared.services.hibp.hibp_service import HibpService


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

        enterprises = Enterprise.objects.filter(locked=False)
        for enterprise in enterprises:
            members = enterprise.enterprise_members.filter(
                is_activated=True, user__is_leaked=False
            ).select_related('user')
            for member in members:
                user = member.user
                email = user.get_from_cystack_id().get("email")
                if not email:
                    continue
                hibp_check = HibpService().check_breach(email=email)
                if hibp_check:
                    user.is_leaked = True
                    user.save()

    def scheduling(self):
        schedule.every().day.at("19:00").do(self.run)
        while True:
            schedule.run_pending()
            time.sleep(1)
