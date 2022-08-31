import json
import uuid

import humps
import requests
import stripe
from django.conf import settings

from django.core.management import BaseCommand

from cystack_models.models import *
from shared.constants.transactions import PAYMENT_METHOD_WALLET, PAYMENT_METHOD_CARD
from shared.utils.app import now


class Command(BaseCommand):
    def handle(self, *args, **options):
        stripe_plan_id = "pm_enterprise_monthly"
        customer_id = "cus_MISZ5ad10LCxTJ"
        stripe_subscription_id = "sub_1LaEukKTkvqGIu5IQ0kvx3Pc"
        stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)

        # Cập nhật lại số lượng member mới - cho chu kỳ sau, ko cần thanh toán ngay
        # update_stripe_subscription = stripe.Subscription.modify(
        #     stripe_subscription_id,
        #     proration_behavior='create_prorations',
        #     payment_behavior='default_incomplete',
        #     items=[{
        #         'id': stripe_subscription['items']['data'][0].id,
        #         'plan': stripe_plan_id,
        #         'quantity': 7
        #     }]
        # )

        # Tạo invoice mới:
        # new_change_member_invoice = stripe.Invoice.create(
        #     customer=customer_id,
        #     collection_method="charge_automatically",
        #     pending_invoice_items_behavior="include",
        #     metadata={
        #         "scope": settings.SCOPE_PWD_MANAGER,
        #         "user_id": None,     # Replace user_id here
        #         "added_member_user_ids": []     # List added member user ids
        #     }
        # )
        # print(new_change_member_invoice)
        # # Trả tiền ngay lập tức cho invoice này
        # invoice_id = new_change_member_invoice.get("id")
        # paid_invoice = stripe.Invoice.pay(invoice_id)
        # print(paid_invoice)

        # Ngoài ra có thêm cách add tay thêm invoice items cho future invoice
        # https://stripe.com/docs/billing/invoices/subscription#adding-upcoming-invoice-items
        # new_added_invoice_item = stripe.InvoiceItem.create(
        #     customer=customer_id,
        #     description="{2} member(s) added into Locker Enterprise",
        #     # price=stripe_plan_id,
        #     unit_amount=109,
        #     currency="USD",
        #     quantity=2,
        #     subscription=stripe_subscription_id,
        #     metadata={
        #         "added_user_ids": "801,802"
        #     }
        # )
        # print(new_added_invoice_item)

        # Tạo invoice mới?
        # new_change_member_invoice = stripe.Invoice.create(
        #     customer=customer_id,
        #     collection_method="charge_automatically",
        #     pending_invoice_items_behavior="include",
        #     metadata={
        #         "scope": settings.SCOPE_PWD_MANAGER,
        #         "user_id": None,     # Replace user_id here
        #         # "added_member_user_ids": []     # List added member user ids
        #     }
        # )

        # Trả tiền ngay lập tức cho invoice này
        paid_invoice = stripe.Invoice.pay("in_1LcQ3dKTkvqGIu5I8MTzKnyG")
        print(paid_invoice)