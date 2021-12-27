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
                "alias": PLAN_TYPE_PM_BASIC,
                DURATION_MONTHLY: 399,
                DURATION_HALF_YEARLY: 2394,
                DURATION_YEARLY: 1188
            },
            {
                "alias": PLAN_TYPE_PM_PRO,
                DURATION_MONTHLY: 799,
                DURATION_HALF_YEARLY: 4794,
                DURATION_YEARLY: 4788
            },
            {
                "alias": PLAN_TYPE_PM_FAMILY,
                DURATION_MONTHLY: 1199,
                DURATION_HALF_YEARLY: 7194,
                DURATION_YEARLY: 5988
            },
            {
                "alias": PLAN_TYPE_PM_BUSINESS,
                DURATION_MONTHLY: 599,
                DURATION_HALF_YEARLY: 3594,
                DURATION_YEARLY: 3588
            },
            {
                "alias": PLAN_TYPE_PM_AGENCY,
                DURATION_MONTHLY: 2499,
                DURATION_HALF_YEARLY: 14994,
                DURATION_YEARLY: 11988
            },
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

    def create_pm_stripe(self):
        print("stripe key: ", stripe.api_key)
        personal_product_id = 'prod_JalW7jrL79U5F9'
        personal_monthly_plan = stripe.Plan.create(
            id='{}_monthly'.format(PLAN_TYPE_PM_PERSONAL_PREMIUM),
            amount_decimal=99,
            currency='usd',
            interval='month',
            product=personal_product_id,
        )
        personal_half_yearly_plan = stripe.Plan.create(
            id='{}_half_yearly'.format(PLAN_TYPE_PM_PERSONAL_PREMIUM),
            amount_decimal=99 * 6,
            currency='usd',
            interval='month',
            product=personal_product_id,
            interval_count=6
        )
        personal_yearly_plan = stripe.Plan.create(
            id='{}_yearly'.format(PLAN_TYPE_PM_PERSONAL_PREMIUM),
            amount_decimal=99 * 12,
            currency='usd',
            interval='year',
            product=personal_product_id,
        )

        family_product_id = 'prod_Jalo6lUd77esMN'
        family_monthly_plan = stripe.Plan.create(
            id='{}_monthly'.format(PLAN_TYPE_PM_FAMILY_DISCOUNT),
            amount_decimal=249,
            currency='usd',
            interval='month',
            product=family_product_id,
        )
        family_half_yearly_plan = stripe.Plan.create(
            id='{}_half_yearly'.format(PLAN_TYPE_PM_FAMILY_DISCOUNT),
            amount_decimal=249 * 6,
            currency='usd',
            interval='month',
            product=family_product_id,
            interval_count=6
        )
        family_yearly_plan = stripe.Plan.create(
            id='{}_yearly'.format(PLAN_TYPE_PM_FAMILY_DISCOUNT),
            amount_decimal=249 * 12,
            currency='usd',
            interval='year',
            product=family_product_id,
        )

        business_product_id = 'prod_JalpLx2qWFz3nO'
        business_monthly_plan = stripe.Plan.create(
            id='{}_monthly'.format(PLAN_TYPE_PM_ENTERPRISE),
            amount_decimal=199,
            currency='usd',
            interval='month',
            product=business_product_id,
        )
        business_half_yearly_plan = stripe.Plan.create(
            id='{}_half_yearly'.format(PLAN_TYPE_PM_ENTERPRISE),
            amount_decimal=199 * 6,
            currency='usd',
            interval='month',
            product=business_product_id,
            interval_count=6
        )
        business_yearly_plan = stripe.Plan.create(
            id='{}_yearly'.format(PLAN_TYPE_PM_ENTERPRISE),
            amount_decimal=199 * 12,
            currency='usd',
            interval='year',
            product=business_product_id,
        )

        print("Done")
