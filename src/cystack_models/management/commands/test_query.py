from django.core.management import BaseCommand
from django.db import connection
from django.db.models import Count, When, Case, IntegerField, Q, OuterRef, Subquery, Sum, F, FloatField, Value, \
    CharField

from core.settings import CORE_CONFIG
from cystack_models.models import *
from shared.constants.ciphers import *
from shared.constants.transactions import *


class Command(BaseCommand):
    cipher_repository = CORE_CONFIG["repositories"]["ICipherRepository"]()

    def handle(self, *args, **options):
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

        subquery_user_plan = User.objects.filter(user_id=OuterRef('user_id')).annotate(
            plan=F('pm_user_plan__pm_plan__name')
        ).annotate(
            plan_name=Case(
                When(plan__isnull=False, then=F('plan')), default=Value('Free'), output_field=CharField()
            )
        )

        users = User.objects.filter(user_id__in=[3721]).select_related('pm_user_plan__pm_plan')
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
            plan_name=Subquery(
                subquery_user_plan.values_list('plan_name', flat=True)
            )
        )

        for user in users:
            print(user.user_id, user.web_device_count, user.mobile_device_count,
                  user.ios_device_count, user.android_device_count, user.extension_device_count)
            print(user.user_id, "----> Items: ", user.items, user.items_password, user.items_note,
                  user.items_identity, user.items_card, user.items_crypto_backup, user.items_totp)
            print(user.user_id, user.private_emails)
            print(user.user_id, user.paid_money)
            print(user.plan_name)
        print("CONNECTION QUERIES: ", len(connection.queries))
