import traceback
from datetime import datetime

from django.conf import settings
from django.db import close_old_connections, connection
from django.db.models import Count, When, Case, IntegerField, Sum, F, FloatField, Value, Q
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from cystack_models.models import User
from shared.background.i_background import BackgroundThread
from shared.constants.ciphers import *
from shared.constants.transactions import PLAN_TYPE_PM_FREE, PAYMENT_STATUS_PAID
from shared.external_request.requester import requester, RequesterError
from shared.log.cylog import CyLog
from shared.services.spreadsheet.spreadsheet import LockerSpreadSheet
from shared.utils.app import now
from v1_0.apps import PasswordManagerViewSet


class ManagementCommandPwdViewSet(PasswordManagerViewSet):
    authentication_classes = ()
    permission_classes = ()
    http_method_names = ["head", "options", "get", "post"]

    def check_perms(self):
        token = self.request.META.get("HTTP_TOKEN", None)
        if token != settings.MANAGEMENT_COMMAND_TOKEN:
            raise PermissionDenied
        return True

    @action(methods=["post"], detail=False)
    def commands(self, request, *args, **kwargs):
        self.check_perms()
        command_name = kwargs.get("pk")
        if not command_name:
            raise NotFound
        try:
            func = getattr(self, command_name)
        except AttributeError:
            raise ValidationError(detail={"pk": ["This is not a func command"]})
        if not func:
            raise ValidationError(detail={"pk": ["This is not a func command"]})
        if not callable(func):
            raise ValidationError(detail={"pk": ["This is not callable"]})
        close_old_connections()
        func_data = request.data.get("data", {})
        background = request.data.get("background", True)
        # Run background or not this function
        try:
            if background:
                BackgroundThread(task=func, **func_data)
            else:
                result = func(**func_data)
                if result:
                    return Response(status=200, data=result)
        except TypeError as e:
            raise ValidationError(detail={"err": e.__str__()})
        return Response(status=200, data={"id": command_name})

    def set_user_plan(self, user_id, start_period, end_period, cancel_at_period_end, default_payment_method, plan_id,
                      pm_mobile_subscription):
        user = self.user_repository.retrieve_or_create_by_id(user_id=user_id)
        pm_user_plan = self.user_repository.get_current_plan(user=user, scope=settings.SCOPE_PWD_MANAGER)
        pm_user_plan.start_period = start_period
        pm_user_plan.end_period = end_period
        if cancel_at_period_end is not None:
            pm_user_plan.cancel_at_period_end = cancel_at_period_end
        if default_payment_method is not None:
            pm_user_plan.default_payment_method = default_payment_method
        if plan_id is not None:
            pm_user_plan.pm_plan_id = plan_id
        if pm_mobile_subscription is not None:
            pm_user_plan.pm_mobile_subscription = pm_mobile_subscription
        pm_user_plan.save()
        return {
            "user_id":  pm_user_plan.user_id,
            "start_period": pm_user_plan.start_period,
            "end_period": pm_user_plan.end_period,
            "cancel_at_period": pm_user_plan.cancel_at_period_end,
            "default_payment_method": pm_user_plan.default_payment_method,
            "plan_id": pm_user_plan.pm_plan_id,
            "pm_mobile_subscription": pm_user_plan.pm_mobile_subscription
        }

    @action(methods=["get"], detail=False)
    def users(self, request, *args, **kwargs):
        token = self.request.query_params.get("token", None)
        if token != settings.MANAGEMENT_COMMAND_TOKEN:
            raise PermissionDenied
        duration = self.request.query_params.get("duration") or 30
        BackgroundThread(task=self.list_activated_users, **{"duration": duration * 86400})
        statistic_data = self.users_statistic()
        return Response(status=200, data=statistic_data)

    @staticmethod
    def users_statistic():
        current_time = now()
        users = User.objects.filter().select_related('pm_user_plan__pm_plan')

        activated_users = users.filter(activated=True)
        activated_in_30 = activated_users.filter(activated_date__gte=current_time - 30 * 86400).count()
        activated_in_60 = activated_users.filter(activated_date__gte=current_time - 2 * 30 * 86400).count()

        not_login_30 = activated_users.filter(last_request_login__lt=current_time - 30 * 86400).count()
        not_login_60 = activated_users.filter(last_request_login__lt=current_time - 2 * 30 * 86400).count()

        deleted_users = users.filter(delete_account_date__isnull=False)
        deleted_in_30 = deleted_users.filter(delete_account_date__gte=current_time - 30 * 86600).count()
        deleted_in_60 = deleted_users.filter(delete_account_date__gte=current_time - 2 * 30 * 86600).count()

        total_activate_users_not_deleted = activated_users.exclude(
            user_id__in=list(deleted_users.values_list('user_id', flat=True))
        ).count()

        total_activate_users = activated_users.count()

        statistic_data = {
            "total_activate_users": total_activate_users,
            "total_activate_users_not_deleted": total_activate_users_not_deleted,
            "activated": {
                "in_30": activated_in_30,
                "in_60": activated_in_60
            },
            "not_login": {
                "in_30": not_login_30,
                "in_60": not_login_60
            },
            "deleted": {
                "in_30": deleted_in_30,
                "in_60": deleted_in_60
            }
        }
        return statistic_data

    def list_activated_users(self, duration):
        try:
            self._list_activated_users(duration)
            print("DONE!!!")
        except Exception as e:
            tb = traceback.format_exc()
            CyLog.error(**{"message": f"[Statistic] list_activated_users error: {tb}"})
        finally:
            connection.close()

    def _list_activated_users(self, duration):
        from_time = now() - duration
        users = User.objects.filter(creation_date__gte=from_time).select_related(
            'pm_user_plan__pm_plan'
        )
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
            )
        ).values('user_id', 'web_device_count', 'mobile_device_count', 'ios_device_count', 'android_device_count',
                 'extension_device_count')
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

        rows = [
            ["User ID", "Email", "Phone", "Country", "Verified", "Created MP", "CS Created date", "LK Created date",
             "Web app", "Android", "iOS", "Extension",
             "Total item(s)", "Passwords", "Notes", "Cards", "Identity", "Crypto Backups", "OTP", "Private emails",
             "Deleted account", "LK Plan", "UTM Source", "Paid", "Number of login"]
        ]
        for user in users:
            # if user.user_id > 10000:
            #     continue
            # else:
            #     print(user.user_id, user.items, user.items_password, user.items_note)
            # continue
            user_id = user.user_id
            user_from_id_data = users_from_id_dict.get(user.user_id) or {}
            use_web = True if users_device_statistic_dict.get(user_id).get("web_device_count", 0) > 0 else False
            use_ios = True if users_device_statistic_dict.get(user_id).get("ios_device_count", 0) > 0 else False
            use_android = True if users_device_statistic_dict.get(user_id).get("android_device_count", 0) > 0 else False
            use_extension = True if users_device_statistic_dict.get(user_id).get("extension_device_count", 0) > 0 else False
            deleted_user = True if user.delete_account_date or user_from_id_data.get("is_deleting") \
                                   or (not user_from_id_data.get("email")) else False
            try:
                plan = user.pm_user_plan.pm_plan.name
            except AttributeError:
                plan = PLAN_TYPE_PM_FREE
            row = [
                user.user_id,
                user_from_id_data.get("email"),
                user_from_id_data.get("phone"),
                user_from_id_data.get("country"),
                user_from_id_data.get("verified"),
                user.activated,
                self._time_from_ts(user_from_id_data.get("registered_time")),
                self._time_from_ts(user.creation_date),

                use_web, use_android, use_ios, use_extension,

                # "Total item(s)", "Passwords", "Notes", "Cards", "Identity", "Crypto Backups", "OTP", "Private emails"
                users_cipher_statistic_dict.get(user_id).get("items"),
                users_cipher_statistic_dict.get(user_id).get("items_password"),
                users_cipher_statistic_dict.get(user_id).get("items_note"),
                users_cipher_statistic_dict.get(user_id).get("items_card"),
                users_cipher_statistic_dict.get(user_id).get("items_identity"),
                users_cipher_statistic_dict.get(user_id).get("items_crypto_backup"),
                users_cipher_statistic_dict.get(user_id).get("items_totp"),
                users_private_email_statistic_dict.get(user_id).get("private_emails"),

                # "Deleted account", "LK Plan", "UTM Source", "Paid", "Number of login"
                deleted_user,
                plan,
                user_from_id_data.get("utm_source"),
                users_paid_statistic_dict.get(user_id).get("paid_money"),
                ""
            ]
            rows.append(row)

        print("Total queries: ", len(connection.queries))
        locker_spreadsheet = LockerSpreadSheet()
        sheet = locker_spreadsheet.add_sheet(f"Users {round(duration / 86400)} days - {now()}")
        sheet.append_rows(rows)

    @staticmethod
    def _time_from_ts(ts):
        try:
            ts = int(ts)
            return datetime.utcfromtimestamp(ts).strftime('%H:%M:%S %d-%m-%Y')
        except (AttributeError, TypeError, ValueError):
            return None
