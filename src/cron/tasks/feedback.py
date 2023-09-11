import os
import time
import schedule
import requests
from datetime import datetime

from django.conf import settings
from django.db import close_old_connections
from django.db.models import OuterRef, Subquery, CharField, FloatField

from cron.task import Task
from cystack_models.models.users.users import User
from cystack_models.models.users.devices import Device
from cystack_models.models.payments.payments import Payment
from shared.background import LockerBackgroundFactory, BG_NOTIFY
from shared.constants.transactions import PAYMENT_STATUS_PAID, PLAN_TYPE_PM_ENTERPRISE
from shared.log.cylog import CyLog
from shared.services.spreadsheet.spreadsheet import LockerSpreadSheet, HEADERS, API_USERS
from shared.utils.app import now


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
        # try:
        #     self.asking_for_feedback_after_subscription()
        # except Exception as e:
        #     self.logger.error()
        # self.upgrade_survey_emails()

    def upgrade_survey_emails(self):
        spread_sheet = LockerSpreadSheet()
        spread_sheet.upgrade_survey_email()

    def asking_for_feedback_after_subscription(self):
        payments = Payment.objects.filter(
            user_id=OuterRef("user_id"), total_price__gt=0,
            status=PAYMENT_STATUS_PAID
        ).order_by('created_time')
        users = User.objects.filter(activated=True).annotate(
            first_payment_date=Subquery(payments.values('created_time')[:1], output_field=FloatField()),
            first_payment_plan=Subquery(payments.values('plan')[:1], output_field=CharField()),
        ).exclude(first_payment_date__isnull=True).filter(
            first_payment_date__gte=now() - 30 * 86400,
            first_payment_date__lt=now() - 29 * 86400
        ).values('user_id', 'first_payment_plan')
        for user in users:
            if user.get("first_payment_plan") == PLAN_TYPE_PM_ENTERPRISE:
                review_url = "https://www.g2.com/products/locker-password-manager/reviews#reviews"
            else:
                review_url = "https://www.trustpilot.com/review/locker.io?sort=recency&utm_medium=trustbox&utm_source=MicroReviewCount"
            LockerBackgroundFactory.get_background(bg_name=BG_NOTIFY, background=False).run(
                func_name="notify_locker_mail", **{
                    "user_ids": [user.get("user_id")],
                    "job": "asking_for_feedback_after_subscription",
                    "scope": settings.SCOPE_PWD_MANAGER,
                    "review_url": review_url,
                }
            )

    def log_new_users(self):
        current_time = now()
        current_time_str = datetime.fromtimestamp(now()).strftime("%d-%b-%Y")

        devices = Device.objects.filter(user_id=OuterRef("user_id")).order_by('last_login')
        users = User.objects.filter(activated=True)
        new_users = users.filter(
            activated=True,
            activated_date__lte=current_time, activated_date__gt=current_time - 86400
        ).annotate(
            first_device_client_id=Subquery(devices.values('client_id')[:1], output_field=CharField()),
            first_device_name=Subquery(devices.values('device_name')[:1], output_field=CharField()),
        ).order_by('activated_date').values('user_id', 'first_device_client_id', 'first_device_name')

        user_ids = [new_user.get("user_id") for new_user in new_users]
        users_res = requests.post(url=API_USERS, headers=HEADERS, json={"ids": user_ids, "emails": []})
        if users_res.status_code != 200:
            CyLog.error(**{"message": "[log_new_users] Get users from Gateway error: {} {}".format(
                users_res.status_code, users_res.text
            )})
            users_data = []
        else:
            users_data = users_res.json()

        notification = ""
        for new_user in new_users:
            user_data = next(
                (item for item in users_data if item["id"] == new_user.get("user_id")), {}
            )
            notification += "{} - {} - {}\n".format(
                user_data.get("email") or new_user.get("user_id"),
                new_user.get("first_device_client_id"),
                new_user.get("first_device_name"),
            )

        CyLog.info(**{
            "message": "Date: {}\nTotal: {}\nNew users: {}\n{}".format(
                current_time_str, users.count(), len(new_users), notification
            ),
            "output": ["slack_new_users"]
        })

    def scheduling(self):
        if os.getenv("PROD_ENV") != "staging":
            schedule.every().day.at("10:00").do(self.run)
            while True:
                schedule.run_pending()
                time.sleep(1)
