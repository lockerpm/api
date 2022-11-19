import json
import uuid
from datetime import datetime

import humps
import requests

from django.core.management import BaseCommand
from django.db.models import Count, When, Case, IntegerField, Q

from core.settings import CORE_CONFIG
from cystack_models.models import *
from shared.constants.ciphers import *
from shared.constants.transactions import PAYMENT_METHOD_WALLET, PAYMENT_METHOD_CARD
from shared.utils.app import now


class Command(BaseCommand):
    cipher_repository = CORE_CONFIG["repositories"]["ICipherRepository"]()

    def handle(self, *args, **options):
        self.list_activated_users(duration=14 * 86400)
        self.list_activated_users(duration=30 * 86400)

        self.count_not_login_users(duration=30 * 86400)
        self.count_not_login_users(duration=30 * 86400 * 2)

        self.count_deleted_users(duration=30 * 86400)
        self.count_deleted_users(duration=30 * 86400 * 2)

        self.count_total_users_exclude_deleted()

        self.count_total_users()

    def list_activated_users(self, duration):
        # Query activated users from (now - duration) to now
        from_time = now() - duration
        users = User.objects.filter(activated=True).filter(
            activated_date__gte=from_time
        ).annotate(
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
        )
        users_data = []
        print("Total: ", users.count(), users.first(), users.last())
        for user in users:
            user_from_id_data = user.get_from_cystack_id()
            user_data = {
                "user_id": user.user_id,
                "email": user_from_id_data.get("email"),
                "activated_date": user.activated_date,
                "last_login": user.last_request_login,
                "web_device_count": user.web_device_count,
                "ios_device_count": user.ios_device_count,
                "android_device_count": user.android_device_count,
                "extension_device_count": user.extension_device_count,
                "used_platforms": {
                    "web": True if user.web_device_count > 0 else False,
                    "ios": True if user.ios_device_count > 0 else False,
                    "android": True if user.android_device_count > 0 else False,
                    "extension": True if user.extension_device_count > 0 else False,
                }
            }

            ciphers = self.cipher_repository.get_multiple_by_user(
                user=user, exclude_team_ids=[]
            ).order_by('-revision_date').values('type').annotate(count=Count('type')).order_by('-count')
            ciphers_count = {item["type"]: item["count"] for item in list(ciphers)}
            user_data["items"] = ciphers_count
            user_data["total_private_emails"] = user.relay_addresses.filter(enabled=True).count()

            users_data.append(user_data)
            print("Done: ", user.user_id)

        with open(f'last_activated_{round(duration/86400)}.csv', 'w', encoding="utf-8") as f:
            head = "User ID,Email,Activated date,Last login,Used platforms," \
                   "Password,Note,Identity,Card,OTP,Crypto Backup,Private Emails"
            print(head, file=f)
            for user_data in users_data:
                used_platforms = []
                for key, value in user_data.get("used_platforms").items():
                    if value is True:
                        used_platforms.append(key)
                activated_date_str = self._time_from_ts(user_data.get("activated_date"))
                last_login_str = self._time_from_ts(user_data.get("last_login"))
                line = f'{user_data.get("user_id")},{user_data.get("email")},' \
                       f'{activated_date_str},{last_login_str},{used_platforms},' \
                       f'{user_data.get("items").get(CIPHER_TYPE_LOGIN, 0)},' \
                       f'{user_data.get("items").get(CIPHER_TYPE_NOTE, 0)},' \
                       f'{user_data.get("items").get(CIPHER_TYPE_IDENTITY, 0)},' \
                       f'{user_data.get("items").get(CIPHER_TYPE_CARD, 0)},' \
                       f'{user_data.get("items").get(CIPHER_TYPE_TOTP, 0)},' \
                       f'{user_data.get("items").get(CIPHER_TYPE_CRYPTO_WALLET, 0)},' \
                       f'{user_data.get("total_private_emails")},'
                print(line, file=f)

    @staticmethod
    def _time_from_ts(ts):
        try:
            ts = int(ts)
            return datetime.utcfromtimestamp(ts).strftime('%H:%M:%S %d-%m-%Y')
        except (AttributeError, TypeError, ValueError):
            return None
        except Exception:
            print("Error: ", ts)
            return None

    def count_not_login_users(self, duration):
        from_time = now() - duration
        users = User.objects.filter(activated=True).filter(
            activated_date__gte=from_time
        ).filter(
            Q(last_requet_login__isnull=True) | Q(last_request_login__lt=from_time)
        ).distinct().count()
        print(f"[+] So user khong dang nhap trong {round(duration/86400)} ngay qua la: {users}")

    def count_deleted_users(self, duration):
        from_time = now() - duration
        users = User.objects.filter(delete_account_date__isnull=False).filter(
            delete_account_date__gte=from_time
        )
        print(f"[+] So user xoa tai khoan trong {round(duration/86400)} ngay qua la: {users}")

    def count_total_users_exclude_deleted(self):
        users = User.objects.filter(activated=True).count()
        print(f"[+] Tong so users (activated - khong tinh deleted): {users}")

    def count_total_users(self):
        # Deleted:
        users = User.objects.filter().count()
        print(f"[+] Tong so users: {users}")


