import json
import uuid
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import humps
import requests

from django.core.management import BaseCommand
from django.db.models import Count, When, Case, IntegerField, Q, F, CharField, ExpressionWrapper, DateTimeField
from django.db.models.functions import TruncMonth, TruncYear, Concat, Cast

from core.settings import CORE_CONFIG
from cystack_models.models import *
from shared.constants.ciphers import *
from shared.constants.transactions import PAYMENT_METHOD_WALLET, PAYMENT_METHOD_CARD
from shared.utils.app import now


class Command(BaseCommand):
    cipher_repository = CORE_CONFIG["repositories"]["ICipherRepository"]()

    def handle(self, *args, **options):
        users = User.objects.all()

        created_mp_users = users.filter(activated=True)
        total_created_mp_users = created_mp_users.count()
        print("Tong so luong user da tao MP: ", total_created_mp_users)


        tb_month = created_mp_users.filter(activated_date__gte=1648573200)
        print("TB thang: ", tb_month.count() / 12)
        print("TB ngay: ", tb_month.count() / (12 * 30))

        start_date = datetime(2022, 1, 1)
        end_date = datetime(2023, 4, 1)

        total_month_active = 0
        while True:
            start_date_ts = start_date.timestamp()
            end_date_ts = end_date.timestamp()
            if start_date_ts > end_date_ts:
                break
            next_start_date = start_date + relativedelta(months=+1)

            month_activate_users = created_mp_users.exclude(revision_date__isnull=True).filter(
                revision_date__gte=start_date_ts, revision_date__lt=next_start_date.timestamp()
            ).count()

            total_month_active += month_activate_users
            print("month_activate_users: ", month_activate_users)


            month_activate_users = created_mp_users.filter(
                activated_date__gte=start_date_ts, activated_date__lt=next_start_date.timestamp()
            )

            print("- Active users: {} - Total: {} - Avg: {}".format(
                start_date,
                month_activate_users.count(),
                round(month_activate_users.count()/30)
            ))
            start_date = next_start_date
        print("total_month_active: ", total_month_active)

        # by_month_users = created_mp_users.annotate(
        #     activated_date_int=Cast(F('activated_date'), output_field=IntegerField())
        # ).annotate(
        #     # activated_datetime=ExpressionWrapper(F('activated_date_int'), output_field=DateTimeField()),
        #     activated_datetime=Cast(F('activated_date_int'), output_field=DateTimeField())
        # ).values('activated_datetime')
        #     .annotate(
        #     month=TruncMonth('activated_datetime'),
        #     year=TruncYear('activated_datetime')
        # ).annotate(
        #     month_year=Concat(F('month'), F('year'), output_field=CharField())
        # ).values('month_year').annotate(c=Count('month_year')).values(
        #     'month_year', 'c'
        # )
        # print(by_month_users)
