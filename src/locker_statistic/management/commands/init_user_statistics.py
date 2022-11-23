from datetime import datetime

import pytz
from django.conf import settings
from django.core.management import BaseCommand
from django.db.models import Count, Case, When, IntegerField, Sum, F, Value, FloatField

from cystack_models.models import *
from shared.constants.ciphers import *
from shared.constants.transactions import *
from shared.external_request.requester import requester, RequesterError
from locker_statistic.models.user_statistics import UserStatistic


class Command(BaseCommand):
    def handle(self, *args, **options):
        UserStatistic.objects.all().delete()
        users = User.objects.all().order_by('user_id')
        user_ids = list(users.values_list('user_id', flat=True))
        batch_size = 2000
        for i in range(0, len(user_ids), batch_size):
            batch_user_ids = user_ids[i:i + batch_size]
            self.list_users(user_ids=batch_user_ids)

    def list_users(self, user_ids):
        users = User.objects.filter(user_id__in=user_ids).select_related('pm_user_plan__pm_plan')
        users_device_statistic = users.annotate(
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
        ).values('user_id', 'web_device_count', 'mobile_device_count', 'ios_device_count', 'android_device_count',
                 'extension_device_count', 'desktop_device_count')
        users_device_statistic_dict = dict()
        for e in users_device_statistic:
            users_device_statistic_dict.update({e["user_id"]: e})

        users_cipher_statistic = users.annotate(
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
        ).values('user_id', 'items_password', 'items_note', 'items_identity', 'items_card', 'items_crypto_backup',
                 'items_totp', 'items')
        users_cipher_statistic_dict = dict()
        for e in users_cipher_statistic:
            users_cipher_statistic_dict.update({e["user_id"]: e})

        users_private_email_statistic = users.annotate(
            private_emails=Count('relay_addresses')
        ).values('user_id', 'private_emails')
        users_private_email_statistic_dict = dict()
        for e in users_private_email_statistic:
            users_private_email_statistic_dict.update({e["user_id"]: e})

        users_paid_statistic = users.annotate(
            paid_money=Sum(
                Case(
                    When(payments__status=PAYMENT_STATUS_PAID, then=F('payments__total_price')),
                    default=Value(0), output_field=FloatField()
                )
            )
        ).values('user_id', 'paid_money')
        users_paid_statistic_dict = dict()
        for e in users_paid_statistic:
            users_paid_statistic_dict.update({e["user_id"]: e})
        # Request to IDs
        url = "{}/micro_services/users".format(settings.GATEWAY_API)
        headers = {'Authorization': settings.MICRO_SERVICE_USER_AUTH}
        data_send = {"ids": list(users.values_list('user_id', flat=True)), "emails": []}
        res = requester(method="POST", url=url, headers=headers, data_send=data_send, timeout=180)
        if res.status_code != 200:
            raise RequesterError
        users_from_id_data = res.json()
        users_from_id_dict = {}
        if users_from_id_data and isinstance(users_from_id_data, list):
            for u in users_from_id_data:
                users_from_id_dict.update({u["id"]: u})

        user_statistic_objs = []
        for user in users:
            user_id = user.user_id
            user_from_id_data = users_from_id_dict.get(user.user_id) or {}
            use_web = True if users_device_statistic_dict.get(user_id).get("web_device_count", 0) > 0 else False
            use_ios = True if users_device_statistic_dict.get(user_id).get("ios_device_count", 0) > 0 else False
            use_android = True if users_device_statistic_dict.get(user_id).get("android_device_count", 0) > 0 else False
            use_extension = True if users_device_statistic_dict.get(user_id).get("extension_device_count", 0) > 0 else False
            use_desktop = True if users_device_statistic_dict.get(user_id).get("desktop_device_count", 0) > 0 else False

            deleted_account = True if user.delete_account_date or user_from_id_data.get("is_deleting") \
                                      or (not user_from_id_data.get("email")) else False
            try:
                plan = user.pm_user_plan.pm_plan.name
            except AttributeError:
                plan = PLAN_TYPE_PM_FREE

            user_statistic_data = {
                "user_id": user.user_id,
                "country":  user_from_id_data.get("country"),
                "verified": user_from_id_data.get("verified"),
                "created_master_password": user.activated,
                "cs_created_date": self._datetime_from_ts(user_from_id_data.get("registered_time")),
                "lk_created_date": self._datetime_from_ts(user.creation_date),
                "use_web_app": use_web,
                "use_android": use_android,
                "use_ios": use_ios,
                "use_extension": use_extension,
                "use_desktop": use_desktop,
                "total_items": users_cipher_statistic_dict.get(user_id).get("items") or 0,
                "num_password_items": users_cipher_statistic_dict.get(user_id).get("items_password") or 0,
                "num_note_items": users_cipher_statistic_dict.get(user_id).get("items_note") or 0,
                "num_card_items": users_cipher_statistic_dict.get(user_id).get("items_card") or 0,
                "num_identity_items": users_cipher_statistic_dict.get(user_id).get("items_identity") or 0,
                "num_crypto_backup_items": users_cipher_statistic_dict.get(user_id).get("items_crypto_backup") or 0,
                "num_totp_items": users_cipher_statistic_dict.get(user_id).get("items_totp") or 0,
                "num_private_emails": users_private_email_statistic_dict.get(user_id).get("private_emails") or 0,
                "deleted_account": deleted_account,
                "lk_plan": plan,
                "utm_source": user_from_id_data.get("utm_source"),
                "paid_money": users_paid_statistic_dict.get(user_id, {}).get("paid_money") or 0,
            }
            user_statistic_objs.append(
                UserStatistic(**user_statistic_data)
            )
        UserStatistic.objects.bulk_create(user_statistic_objs, batch_size=200, ignore_conflicts=True)

    @staticmethod
    def _datetime_from_ts(ts):
        try:
            ts = int(ts)
            return datetime.fromtimestamp(ts, tz=pytz.UTC)
        except (AttributeError, TypeError, ValueError):
            return None

