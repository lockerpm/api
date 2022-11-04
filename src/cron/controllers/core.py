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
from cron.controllers.tasks.delete_trash_ciphers import delete_trash_ciphers
from cron.controllers.tasks.domain_verification import domain_verification
from cron.controllers.tasks.enterprise_breach_scan import enterprise_breach_scan
from cron.controllers.tasks.enterprise_member_change_billing import enterprise_member_change_billing
from cron.controllers.tasks.tutorial_reminder import tutorial_reminder


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

    def delete_trash_ciphers(self):
        try:
            delete_trash_ciphers()
            self.logger.info("[+] delete_trash_ciphers Done")
        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error("[!] delete_trash_ciphers error: {}".format(tb))
        finally:
            close_old_connections()

    def domain_verification(self):
        try:
            domain_verification()
            self.logger.info("[+] domain_verification Done")
        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error("[!] domain_verification error: {}".format(tb))
        finally:
            close_old_connections()

    def enterprise_breach_scan(self):
        try:
            enterprise_breach_scan()
            self.logger.info("[+] enterprise_breach_scan Done")
        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error("[!] enterprise_breach_scan error: {}".format(tb))
        finally:
            close_old_connections()

    def enterprise_member_change_billing(self):
        try:
            enterprise_member_change_billing()
            self.logger.info("[+] enterprise_member_change_billing Done")
        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error("[!] enterprise_member_change_billing error: {}".format(tb))
        finally:
            close_old_connections()

    def tutorial_notification(self):
        try:
            tutorial_reminder()
            self.logger.info("[+] tutorial_notification Done")
        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error("[!] tutorial_notification error: {}".format(tb))
        finally:
            close_old_connections()

    def start(self):
        schedule.every(10).minutes.do(self.subscription_by_wallet)
        schedule.every().day.at("19:30").do(self.plan_expiring_notification)
        schedule.every().day.at("10:00").do(self.feedback_tasks)
        schedule.every(20).minutes.do(self.emergency_access_approve)
        schedule.every(120).minutes.do(self.domain_verification)
        schedule.every().day.at("19:00").do(self.enterprise_breach_scan)
        schedule.every().day.at("09:30").do(self.enterprise_member_change_billing)
        # schedule.every().day.at("07:30").do(self.tutorial_notification)

        schedule.every().day.at("17:00").do(self.delete_trash_ciphers)
        self.logger.info("[+] Starting Locker cron task")
        while True:
            schedule.run_pending()
            time.sleep(1)
