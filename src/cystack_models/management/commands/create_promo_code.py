import stripe

from django.core.management import BaseCommand
from django.conf import settings

from cystack_models.models import *
from shared.constants.transactions import *
from shared.utils.app import now


class Command(BaseCommand):

    def handle(self, *args, **options):
        promo_type = PROMO_PERCENTAGE
        expired_time = now() + 12 * 30 * 86400  # 12 months
        code = "LKFAMILY50"
        value = 50
        limit_value = None
        duration = 1
        currency = "USD"
        description_en = "50% off on Family & Friends Plan"
        description_vi = "Ưu đãi 50% gói Family & Friends"

        promo_type_obj = PromoCodeType.objects.get(name=promo_type)

        new_promo_code = PromoCode.objects.create(
            created_time=now(),
            expired_time=expired_time,
            remaining_times=10000,
            valid=True,
            code=code,
            value=value,
            limit_value=limit_value,
            duration=duration,
            currency=currency,
            description_en=description_en,
            description_vi=description_vi,
            type=promo_type_obj
        )
        print(new_promo_code.id)
        # Create on Stripe
        # coupon = stripe.Coupon.create(
        #     duration='repeating',
        #     duration_in_months=duration,
        #     id=new_promo_code.id,
        #     percent_off=value,
        #     name=code,
        #     api_key=STRIPE_SECRET_KEY_TEST
        # )
        # print("Coupon: ", coupon)

    def campaign(self):
        pass