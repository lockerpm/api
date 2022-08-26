import stripe

from django.core.management import BaseCommand
from django.conf import settings

from shared.constants.transactions import *


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.create_new_stripe_plan()

    def create_new_stripe_plan(self):
        locker_product_id = "prod_KqrIRSMFaHeKuj"
        durations = [DURATION_MONTHLY, DURATION_HALF_YEARLY, DURATION_YEARLY]
        plans = [
            {
                "alias": PLAN_TYPE_PM_ENTERPRISE,
                DURATION_MONTHLY: 199,
                DURATION_HALF_YEARLY: 1194,
                DURATION_YEARLY: 2388
            },
            # {
            #     "alias": PLAN_TYPE_PM_FAMILY,
            #     DURATION_MONTHLY: 999,
            #     DURATION_HALF_YEARLY: 7188,
            #     DURATION_YEARLY: 5994
            # }
        ]

        for plan in plans:
            for duration in durations:
                stripe_plan = stripe.Plan.create(
                    id='{}_{}'.format(plan["alias"], duration),
                    amount_decimal=plan[duration],
                    currency='usd',
                    interval='year' if duration == DURATION_YEARLY else 'month',
                    interval_count=6 if duration == DURATION_HALF_YEARLY else 1,
                    product=locker_product_id,
                )
                print("Done plan ", plan, duration)
