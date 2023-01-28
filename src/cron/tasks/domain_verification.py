import time
import schedule

from django.db import close_old_connections

from cron.task import Task
from cystack_models.models.enterprises.domains.domains import Domain
from shared.background import LockerBackgroundFactory, BG_DOMAIN
from shared.utils.app import now


class DomainVerification(Task):
    def __init__(self):
        super(DomainVerification, self).__init__()
        self.job_id = 'domain_verification'

    def register_job(self):
        pass

    def log_job_execution(self, run_time: float, exception: str = None, tb: str = None):
        pass

    def real_run(self, *args):
        # Close old connections
        close_old_connections()

        current_time = now()
        # Find the domains aren't verified
        unverified_domains = Domain.objects.filter(verification=False)
        for unverified_domain in unverified_domains:
            is_verify = unverified_domain.check_verification()
            # If this domain is verified => Send notification
            if is_verify is True:
                owner_user_id = unverified_domain.enterprise.enterprise_members.get(is_primary=True).user_id
                LockerBackgroundFactory.get_background(bg_name=BG_DOMAIN, background=False).run(
                    func_name="domain_verified", **{
                        "owner_user_id": owner_user_id,
                        "domain": unverified_domain
                    }
                )
            else:
                # Check the domain is added more than one day?
                if current_time >= unverified_domain.created_time + 86400 and \
                        unverified_domain.is_notify_failed is False:
                    owner_user_id = unverified_domain.enterprise.enterprise_members.get(is_primary=True).user_id
                    LockerBackgroundFactory.get_background(bg_name=BG_DOMAIN, background=False).run(
                        func_name="domain_unverified", **{
                            "owner_user_id": owner_user_id,
                            "domain": unverified_domain
                        }
                    )
                    unverified_domain.is_notify_failed = True
                    unverified_domain.save()

    def scheduling(self):
        schedule.every(120).minutes.do(self.run)
        while True:
            schedule.run_pending()
            time.sleep(1)
