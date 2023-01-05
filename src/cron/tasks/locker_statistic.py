import os
import time
import requests
import schedule

from django.conf import settings
from django.db.models import OuterRef, Count, IntegerField, When, Case, Sum, Value, F, FloatField, \
    CharField, Subquery, Q

from cron.task import Task
from cystack_models.models.users.users import User
from locker_statistic.models.user_statistics import UserStatistic
from locker_statistic.models.user_statistics_date import UserStatisticDate
from shared.constants.ciphers import *
from shared.constants.transactions import PAYMENT_STATUS_PAID
from shared.external_request.requester import requester
from shared.log.cylog import CyLog
from shared.utils.app import datetime_from_ts, now


class LockerStatistic(Task):
    def __init__(self):
        super(LockerStatistic, self).__init__()
        self.job_id = 'locker_statistic'

    def register_job(self):
        pass

    def log_job_execution(self, run_time: float, exception: str = None, tb: str = None):
        pass

    def real_run(self, *args):
        current_time = now()
        latest_statistic_date = UserStatisticDate.objects.all().order_by('-id').first()

        if latest_statistic_date:
            latest_user_id = latest_statistic_date.latest_user_id
            latest_statistic_time = latest_statistic_date.created_time
            not_free_users_statistic = UserStatistic.objects.exclude(lk_plan="Free").values_list('user_id', flat=True)
            users = User.objects.filter(
                Q(user_id__gt=latest_user_id) | Q(last_request_login__gte=latest_statistic_time) |
                Q(user_id__in=list(not_free_users_statistic))
            ).order_by('-user_id').distinct()
        else:
            users = User.objects.all().order_by('-user_id')

        # Save the statistic data daily
        user_ids = list(users.values_list('user_id', flat=True))
        batch_size = 2000
        for i in range(0, len(user_ids), batch_size):
            batch_user_ids = user_ids[i:i + batch_size]
            self.list_users_statistic(user_ids=batch_user_ids)

        UserStatisticDate.objects.create(
            created_time=current_time, completed_time=now(), latest_user_id=users.first().user_id
        )

    def list_users_statistic(self, user_ids):
        # Sub queries to count devices, items, private emails, etc...
        subquery_user_devices = User.objects.filter(user_id=OuterRef('user_id')).annotate(
            web_device_count=Count(
                Case(When(user_devices__client_id='web', then=1), output_field=IntegerField())
            ),
            mobile_device_count=Count(
                Case(When(user_devices__client_id='mobile', then=1), output_field=IntegerField())
            ),
            ios_device_count=Count(
                Case(When(user_devices__device_type=1, then=1), output_field=IntegerField())
            ),
            android_device_count=Count(
                Case(When(user_devices__device_type=0, then=1), output_field=IntegerField())
            ),
            extension_device_count=Count(
                Case(When(user_devices__client_id='browser', then=1), output_field=IntegerField())
            ),
            desktop_device_count=Count(
                Case(When(user_devices__client_id='desktop', then=1), output_field=IntegerField())
            )
        )

        subquery_user_ciphers = User.objects.filter(user_id=OuterRef('user_id')).annotate(
            items_password=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_LOGIN, then=1), output_field=IntegerField())
            ),
            items_note=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_NOTE, then=1), output_field=IntegerField())
            ),
            items_identity=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_IDENTITY, then=1), output_field=IntegerField())
            ),
            items_card=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_CARD, then=1), output_field=IntegerField())
            ),
            items_crypto_backup=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_CRYPTO_WALLET, then=1), output_field=IntegerField())
            ),
            items_totp=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_TOTP, then=1), output_field=IntegerField())
            ),
            items=Count('created_ciphers'),
        )

        subquery_user_private_emails = User.objects.filter(user_id=OuterRef('user_id')).annotate(
            private_emails=Count('relay_addresses')
        )

        subquery_user_payments = User.objects.filter(user_id=OuterRef('user_id')).annotate(
            paid_money=Sum(
                Case(
                    When(payments__status=PAYMENT_STATUS_PAID, then=F('payments__total_price')),
                    default=Value(0), output_field=FloatField()
                )
            )
        )

        subquery_paid_platforms = User.objects.filter(user_id=OuterRef('user_id')).annotate(
            web_paid_count=Count(
                Case(
                    When(Q(payments__status=PAYMENT_STATUS_PAID, payments__stripe_invoice_id__isnull=False), then=1),
                    output_field=IntegerField()
                )
            ),
            ios_paid_count=Count(
                Case(
                    When(Q(payments__status=PAYMENT_STATUS_PAID, payments__mobile_invoice_id__startswith="GPA."), then=1),
                    output_field=IntegerField()
                )
            ),
            android_paid_count=Count(
                Case(
                    When(Q(payments__status=PAYMENT_STATUS_PAID, payments__mobile_invoice_id__regex=r'^\d+'), then=1),
                    output_field=IntegerField()
                )
            )
        )

        subquery_user_plan = User.objects.filter(user_id=OuterRef('user_id')).annotate(
            plan=F('pm_user_plan__pm_plan__name')
        ).annotate(
            plan_name=Case(
                When(plan__isnull=False, then=F('plan')), default=Value('Free'), output_field=CharField()
            )
        )

        users = User.objects.filter(user_id__in=user_ids).select_related('pm_user_plan__pm_plan')
        users = users.order_by().annotate(
            web_device_count=Subquery(
                subquery_user_devices.values_list('web_device_count', flat=True)
            ),
            mobile_device_count=Subquery(
                subquery_user_devices.values_list('mobile_device_count', flat=True)
            ),
            ios_device_count=Subquery(
                subquery_user_devices.values_list('ios_device_count', flat=True)
            ),
            android_device_count=Subquery(
                subquery_user_devices.values_list('android_device_count', flat=True)
            ),
            extension_device_count=Subquery(
                subquery_user_devices.values_list('extension_device_count', flat=True)
            ),
            desktop_device_count=Subquery(
                subquery_user_devices.values_list('desktop_device_count', flat=True)
            )
        ).annotate(
            items_password=Subquery(
                subquery_user_ciphers.values_list('items_password', flat=True)
            ),
            items_note=Subquery(
                subquery_user_ciphers.values_list('items_note', flat=True)
            ),
            items_identity=Subquery(
                subquery_user_ciphers.values_list('items_identity', flat=True)
            ),
            items_card=Subquery(
                subquery_user_ciphers.values_list('items_card', flat=True)
            ),
            items_crypto_backup=Subquery(
                subquery_user_ciphers.values_list('items_crypto_backup', flat=True)
            ),
            items_totp=Subquery(
                subquery_user_ciphers.values_list('items_totp', flat=True)
            ),
            items=Subquery(
                subquery_user_ciphers.values_list('items', flat=True)
            )
        ).annotate(
            private_emails=Subquery(
                subquery_user_private_emails.values_list('private_emails', flat=True)
            )
        ).annotate(
            paid_money=Subquery(
                subquery_user_payments.values_list('paid_money', flat=True)
            )
        ).annotate(
            web_paid_count=Subquery(
                subquery_paid_platforms.values_list('web_paid_count', flat=True)
            ),
            ios_paid_count=Subquery(
                subquery_paid_platforms.values_list('ios_paid_count', flat=True)
            ),
            android_paid_count=Subquery(
                subquery_paid_platforms.values_list('android_paid_count', flat=True)
            )
        ).annotate(
            plan_name=Subquery(
                subquery_user_plan.values_list('plan_name', flat=True)
            )
        )

        # Request to IDs
        url = "{}/micro_services/users".format(settings.GATEWAY_API)
        headers = {'Authorization': settings.MICRO_SERVICE_USER_AUTH}
        data_send = {"ids": list(users.values_list('user_id', flat=True)), "emails": [], "lk_referral_count": True}
        try:
            res = requester(method="POST", url=url, headers=headers, data_send=data_send, timeout=180)
            if res.status_code != 200:
                CyLog.warning(
                    **{"message": "[Cron] Get user data from ID error: {} {}".format(res.status_code, res.text)})
                return
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout):
            CyLog.warning(**{"message": "[Cron] Get user data from ID error: REQUESTS exception"})
            return

        users_from_id_data = res.json()
        users_from_id_dict = {}
        if users_from_id_data and isinstance(users_from_id_data, list):
            for u in users_from_id_data:
                users_from_id_dict.update({u["id"]: u})

        user_statistic_dicts = {}
        for user in users:
            user_from_id_data = users_from_id_dict.get(user.user_id) or {}

            use_web = True if user.web_device_count > 0 else False
            use_ios = True if user.ios_device_count > 0 else False
            use_android = True if user.android_device_count > 0 else False
            use_extension = True if user.extension_device_count > 0 else False
            use_desktop = True if user.desktop_device_count > 0 else False

            deleted_account = True if user.delete_account_date or user_from_id_data.get("is_deleting") \
                                      or (not user_from_id_data.get("email")) else False

            paid_platforms = []
            if user.web_paid_count > 0:
                paid_platforms.append("web")
            if user.ios_paid_count > 0:
                paid_platforms.append("ios")
            if user.android_paid_count > 0:
                paid_platforms.append("android")
            paid_platforms_str = ",".join(paid_platforms)

            user_statistic_data = {
                "user_id": user.user_id,
                "country": user_from_id_data.get("country"),
                "verified": user_from_id_data.get("verified") or False,
                "created_master_password": user.activated,
                "cs_created_date": datetime_from_ts(user_from_id_data.get("registered_time")),
                "lk_created_date": datetime_from_ts(user.creation_date),
                "lk_last_login": datetime_from_ts(user.last_request_login),
                "use_web_app": use_web,
                "use_android": use_android,
                "use_ios": use_ios,
                "use_extension": use_extension,
                "use_desktop": use_desktop,
                "total_items": user.items,
                "num_password_items": user.items_password,
                "num_note_items": user.items_note,
                "num_card_items": user.items_card,
                "num_identity_items": user.items_identity,
                "num_crypto_backup_items": user.items_crypto_backup,
                "num_totp_items": user.items_totp,
                "num_private_emails": user.private_emails,
                "deleted_account": deleted_account,
                "lk_plan": user.plan_name,
                "lk_referral_count": user_from_id_data.get("lk_referral_count") or 0,
                "utm_source": user_from_id_data.get("utm_source"),
                "paid_money": user.paid_money,
                "paid_platforms": paid_platforms_str
            }
            user_statistic_dict_data = user_statistic_data.copy()
            user_statistic_dict_data.pop('user_id', None)
            user_statistic_dicts.update({user.user_id: user_statistic_dict_data})

        # Bulk update or create django
        UserStatistic.bulk_update_or_create(
            common_keys={},
            unique_key_name='user_id',
            unique_key_to_defaults=user_statistic_dicts,
            batch_size=200,
            ignore_conflicts=True
        )

    def scheduling(self):
        # Only PROD
        if os.getenv("PROD_ENV") == "prod":
            schedule.every().day.at("17:00").do(self.run)
            while True:
                schedule.run_pending()
                time.sleep(1)
