"""
This file implements some cron tasks:
- pm_subscription: Notify expiring plans (7days) & Downgrade plan when users pay failed at the end of period

"""

from cron.controllers.utils.django_config import django_config
django_config()

import schedule
import time
import traceback

from django.db import close_old_connections

from cron.controllers.utils.logger import Logger
from cron.controllers.tasks.pm_subscription import pm_subscription, pm_expiring_notify
from cron.controllers.tasks.emergency_access_auto_approve import emergency_access_auto_approve
from cron.controllers.tasks.feedback import upgrade_survey_emails, log_new_users


class CronTask:
    def __init__(self):
        self.logger = Logger()

    def subscription_by_wallet(self):
        try:
            pm_subscription()
            self.logger.info("[+] subscription_by_wallet Done")
        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error("[!] subscription_by_wallet error: {}".format(tb))
        finally:
            close_old_connections()

    def plan_expiring_notification(self):
        try:
            pm_expiring_notify()
            self.logger.info("[+] pm_expiring_notify Done")
        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error("[!] pm_expiring_notify error: {}".format(tb))
        finally:
            close_old_connections()

    def emergency_access_approve(self):
        try:
            emergency_access_auto_approve()
            self.logger.info("[+] emergency_access_approve Done")
        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error("[!] emergency_access_approve error: {}".format(tb))
        finally:
            close_old_connections()

    def feedback_tasks(self):
        try:
            log_new_users()
            upgrade_survey_emails()
            self.logger.info("[+] feedback_tasks Done")
        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error("[!] feedback_tasks error: {}".format(tb))
        finally:
            close_old_connections()

    def start(self):
        schedule.every(180).minutes.do(self.subscription_by_wallet)
        schedule.every().day.at("19:30").do(self.plan_expiring_notification)
        schedule.every().day.at("10:00").do(self.feedback_tasks)
        schedule.every(20).minutes.do(self.emergency_access_approve)
        self.logger.info("[+] Starting Platform cron task")
        while True:
            schedule.run_pending()
            time.sleep(1)
