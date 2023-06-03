import random
import string

from django.core.management import BaseCommand

from core.settings import CORE_CONFIG
from cystack_models.models import *
from shared.constants.transactions import *
from shared.utils.app import now


class Command(BaseCommand):
    cipher_repository = CORE_CONFIG["repositories"]["ICipherRepository"]()

    def handle(self, *args, **options):
        self.migrate_saas_codes()
        self.create_deal_fuel_saas_promo_code()

    @staticmethod
    def migrate_saas_codes():
        saas_codes = PromoCode.objects.filter(is_saas_code=True)
        saas_codes.filter(code__startswith="SC-").update(saas_market_id=1, saas_plan=PLAN_TYPE_PM_LIFETIME)
        saas_codes.filter(code__startswith="PG-").update(saas_market_id=2, saas_plan=PLAN_TYPE_PM_LIFETIME)

    @staticmethod
    def create_deal_fuel_saas_promo_code():
        codes = []
        promo_type = PROMO_PERCENTAGE
        promo_type_obj = PromoCodeType.objects.get(name=promo_type)
        promo_code_objs = []
        for _ in range(2000):
            expired_time = now() + 365 * 86400
            value = 100
            limit_value = None
            duration = 1
            currency = "USD"
            description_en = "DealFuel Premium code"
            description_vi = "DealFuel Premium code"
            code = ''.join([
                random.choice(string.digits + string.ascii_lowercase + string.ascii_uppercase) for _ in range(8)
            ])
            promo_code_objs.append(PromoCode(
                created_time=now(),
                expired_time=expired_time,
                remaining_times=1,
                valid=True,
                code=f"DF-{code}",
                value=value,
                limit_value=limit_value,
                duration=duration,
                currency=currency,
                description_en=description_en,
                description_vi=description_vi,
                type=promo_type_obj,
                is_saas_code=True,
                saas_market_id=3,
                saas_plan=PLAN_TYPE_PM_PREMIUM
            ))
        for _ in range(2000):
            expired_time = now() + 365 * 86400
            value = 100
            limit_value = None
            duration = 1
            currency = "USD"
            description_en = "DealFuel Family code"
            description_vi = "DealFuel Family code"
            code = ''.join([
                random.choice(string.digits + string.ascii_lowercase + string.ascii_uppercase) for _ in range(8)
            ])
            promo_code_objs.append(PromoCode(
                created_time=now(),
                expired_time=expired_time,
                remaining_times=1,
                valid=True,
                code=f"DF-{code}",
                value=value,
                limit_value=limit_value,
                duration=duration,
                currency=currency,
                description_en=description_en,
                description_vi=description_vi,
                type=promo_type_obj,
                is_saas_code=True,
                saas_market_id=3,
                saas_plan=PLAN_TYPE_PM_FAMILY
            ))
        PromoCode.objects.bulk_create(promo_code_objs, batch_size=200, ignore_conflicts=True)
        print(len(codes))

    @staticmethod
    def migrate_default_timeout():
        User.objects.filter(timeout=15).update(timeout=20160)
