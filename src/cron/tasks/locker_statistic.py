import os
import time
import requests
import schedule

from django.conf import settings
from django.db import close_old_connections
from django.db.models import OuterRef, Count, IntegerField, When, Case, Sum, Value, F, FloatField, \
    CharField, Subquery, Q, Min

from cron.task import Task
from cystack_models.models.users.users import User
from cystack_models.models.user_plans.pm_user_plan_family import PMUserPlanFamily
from locker_statistic.models.user_statistics import UserStatistic
from locker_statistic.models.user_plan_family import UserPlanFamily
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
        # Close old connections
        close_old_connections()

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

        # Update family members
        self.update_plan_family_statistic()

        UserStatisticDate.objects.create(
            created_time=current_time, completed_time=now(), latest_user_id=users.first().user_id
        )

    @staticmethod
    def list_users_statistic(user_ids):
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
            items_crypto_account=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_CRYPTO_ACCOUNT, then=1), output_field=IntegerField())
            ),
            items_driver_license=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_DRIVER_LICENSE, then=1), output_field=IntegerField())
            ),
            items_citizen_id=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_CITIZEN_ID, then=1), output_field=IntegerField())
            ),
            items_passport=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_PASSPORT,  then=1), output_field=IntegerField())
            ),
            items_social_security_number=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_SOCIAL_SECURITY_NUMBER, then=1), output_field=IntegerField())
            ),
            items_wireless_router=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_WIRELESS_ROUTER, then=1), output_field=IntegerField())
            ),
            items_server=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_SERVER, then=1), output_field=IntegerField())
            ),
            items_api=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_API, then=1), output_field=IntegerField())
            ),
            items_database=Count(
                Case(When(created_ciphers__type=CIPHER_TYPE_DATABASE, then=1), output_field=IntegerField())
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

        subquery_first_paid_date = User.objects.filter(user_id=OuterRef('user_id')).annotate(
            first_paid_date=Min('payments__created_time', filter=Q(payments__total_price__gt=0, payments__discount=0))
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
            items_crypto_account=Subquery(
                subquery_user_ciphers.values_list('items_crypto_account', flat=True)
            ),
            items_driver_license=Subquery(
                subquery_user_ciphers.values_list('items_driver_license', flat=True)
            ),
            items_citizen_id=Subquery(
                subquery_user_ciphers.values_list('items_citizen_id', flat=True)
            ),
            items_passport=Subquery(
                subquery_user_ciphers.values_list('items_passport', flat=True)
            ),
            items_social_security_number=Subquery(
                subquery_user_ciphers.values_list('items_social_security_number', flat=True)
            ),
            items_wireless_router=Subquery(
                subquery_user_ciphers.values_list('items_wireless_router', flat=True)
            ),
            items_server=Subquery(
                subquery_user_ciphers.values_list('items_server', flat=True)
            ),
            items_api=Subquery(
                subquery_user_ciphers.values_list('items_api', flat=True)
            ),
            items_database=Subquery(
                subquery_user_ciphers.values_list('items_database', flat=True)
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
            first_payment_date=Subquery(
                subquery_first_paid_date.values_list('first_paid_date', flat=True)
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

            try:
                personal_trial_web_applied = user.pm_user_plan.personal_trial_web_applied
            except AttributeError:
                personal_trial_web_applied = False
            try:
                personal_trial_mobile_applied = user.pm_user_plan.personal_trial_mobile_applied
            except AttributeError:
                personal_trial_mobile_applied = False

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
                "num_crypto_account_items": user.items_crypto_account,
                "num_driver_license_items": user.items_driver_license,
                "num_citizen_id_items": user.items_citizen_id,
                "num_passport_items": user.items_passport,
                "num_social_security_number_items": user.items_social_security_number,
                "num_wireless_router": user.items_wireless_router,
                "num_server_items": user.items_server,
                "num_api_items": user.items_api,
                "num_database_items": user.items_database,
                "num_private_emails": user.private_emails,
                "deleted_account": deleted_account,
                "lk_plan": user.plan_name,
                "lk_referral_count": user_from_id_data.get("lk_referral_count") or 0,
                "utm_source": user_from_id_data.get("utm_source"),
                "paid_money": user.paid_money,
                "first_payment_date": datetime_from_ts(user.first_payment_date),
                "paid_platforms": paid_platforms_str,
                "personal_trial_mobile_applied": personal_trial_mobile_applied,
                "personal_trial_web_applied": personal_trial_web_applied
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

    @staticmethod
    def update_plan_family_statistic():
        pm_user_plans_family = list(PMUserPlanFamily.objects.order_by().values(
            'id', 'created_time', 'email', 'user_id', 'root_user_plan_id'
        ))
        user_plan_family = []
        for pm_user_plan_family in pm_user_plans_family:
            user_plan_family.append(
                UserPlanFamily(
                    id=pm_user_plan_family.get("id"),
                    created_time=pm_user_plan_family.get("created_time"),
                    email=pm_user_plan_family.get("email"),
                    user_id=pm_user_plan_family.get("user_id"),
                    root_user_id=pm_user_plan_family.get("root_user_plan_id")
                )
            )
        UserPlanFamily.objects.bulk_create(user_plan_family, ignore_conflicts=True, batch_size=100)
        existed_ids = [p.get("id") for p in pm_user_plans_family]
        UserPlanFamily.objects.exclude(id__in=existed_ids).delete()

    def scheduling(self):
        # Only PROD
        if os.getenv("PROD_ENV") == "prod":
            schedule.every().day.at("17:00").do(self.run)
            while True:
                schedule.run_pending()
                time.sleep(1)
