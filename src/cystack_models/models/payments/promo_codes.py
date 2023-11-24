import math
import os
import uuid
import stripe
import stripe.error

from django.db import models

from shared.constants.transactions import *
from shared.utils.app import now, random_n_digit
from cystack_models.models.payments.promo_code_types import PromoCodeType
from cystack_models.models.payments.saas_market import SaasMarket
from cystack_models.models.users.users import User


class PromoCode(models.Model):
    """
    This class indicates for a promo code. This is applied when users pay an invoice
    Attributes:
        + id: Unique identifier for the promo code
        + created_time: An integer Unix timestamp indicates for created time of object
        + expired_time
        + remaining_times: Number of remaining times that this object is available
        + valid: default is True. Has the value True if the object is available
        + code: String value of promo code
        + value: The value of promo code
        + limit_value: The limited value
        + duration: Number of intervals for which the coupon repeatedly apply
        + specific_duration: Specific duration type of the `duration` value. The default value is null. Example:
            specific_duration = null
                => `duration` apply for period scope. if duration = 2 => Promo code applies for 2 periods
            specific_duration = 'monthly'
                =>  If duration = 2 => Promo code applies for 2 months (not 2 periods)
        + currency: Specific currency of coupon
        + description_en:
        + description_vi:
        + type: amount_off / percentage_off

    """
    id = models.CharField(primary_key=True, default=uuid.uuid4, max_length=100)
    created_time = models.FloatField(null=True)
    expired_time = models.FloatField()
    remaining_times = models.IntegerField(default=0)
    valid = models.BooleanField(default=True)
    code = models.CharField(max_length=100, null=True, blank=True)  # String that user need send
    value = models.FloatField(default=0)                            # Number is decrease
    limit_value = models.FloatField(null=True)
    duration = models.IntegerField(default=1)  # Number of intervals for which the coupon repeatedly apply
    specific_duration = models.CharField(max_length=128, null=True, default=None)   # Specific duration type
    is_saas_code = models.BooleanField(default=False)
    saas_market = models.ForeignKey(SaasMarket, on_delete=models.SET_NULL, related_name="promo_codes", null=True)
    saas_plan = models.CharField(max_length=128, null=True, default=None)
    currency = models.CharField(max_length=8, default=CURRENCY_USD)
    description_en = models.TextField(default="", blank=True)
    description_vi = models.TextField(default="", blank=True)
    only_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="only_promo_codes", null=True)
    only_period = models.CharField(max_length=128, null=True, default=None)
    only_plan = models.CharField(max_length=128, null=True, default=None)
    type = models.ForeignKey(PromoCodeType, on_delete=models.CASCADE, related_name="promo_codes")

    class Meta:
        db_table = 'cs_promo_codes'

    @classmethod
    def create(cls, **data):
        """
        Create new promo code object
        :param data:
        :return:
        """
        expired_time = data.get("expired_time")
        if not expired_time:
            expired_time = now() + data.get("day_expired") * 86400

        number_code = data['number_code']
        promo_type = data['type']
        code = data['code']
        value = data['value']
        limit_value = data.get("limit_value")
        currency = data.get("currency", "USD")
        duration = data.get("duration", 1)
        specific_duration = data.get("specific_duration")
        description_en = data.get("description_en", "")
        description_vi = data.get("description_vi", "")
        only_user_id = data.get("only_user_id")
        only_period = data.get("only_period")
        only_plan = data.get("only_plan")
        is_saas_code = data.get("is_saas_code", False)
        saas_market_id = data.get("saas_market_id", None)
        saas_plan = data.get("saas_plan")
        if is_saas_code is True:
            saas_plan = saas_plan or PLAN_TYPE_PM_LIFETIME

        new_promo_code = cls(
            created_time=now(), expired_time=expired_time, remaining_times=number_code, code=code,
            value=value, limit_value=limit_value, currency=currency,
            type=PromoCodeType.objects.get(name=promo_type),
            duration=duration, specific_duration=specific_duration,
            description_vi=description_vi, description_en=description_en,
            only_user_id=only_user_id,
            only_period=only_period,
            only_plan=only_plan,
            is_saas_code=is_saas_code, saas_market_id=saas_market_id, saas_plan=saas_plan
        )
        new_promo_code.save()
        return new_promo_code

    @classmethod
    def check_valid(cls, value, current_user, new_duration: str = None, new_plan: str = None):
        """
        Check a promo code value is valid
        :param value:
        :param current_user:
        :param new_duration:
        :param new_plan
        :return:
        """
        try:
            promo_code = cls.objects.get(code=value, valid=True)
            # If promo code was expired or promo code was used by this user?
            if promo_code.expired_time < now() or promo_code.remaining_times <= 0 or promo_code.is_saas_code:
                return False
            if current_user is not None:
                if current_user.payments.filter(promo_code=promo_code).count() > 0:
                    return False
                if promo_code.only_user_id and promo_code.only_user_id != current_user.user_id:
                    return False
            if promo_code.only_period and new_duration and promo_code.only_period != new_duration:
                return False
            if promo_code.only_plan and new_plan and new_plan not in list(promo_code.only_plan.split(",")):
                return False

            if promo_code.only_plan and new_plan and promo_code.only_plan != new_plan:
                return False
            return promo_code
        except cls.DoesNotExist:
            return False

    @classmethod
    def check_saas_valid(cls, value, current_user, new_duration: str = None, new_plan: str = None):
        try:
            promo_code = cls.objects.get(code=value, valid=True)
            # If promo code was expired or promo code was used by this user?
            if promo_code.expired_time < now() or promo_code.remaining_times <= 0 or promo_code.is_saas_code is False:
                return False
            if current_user is not None:
                if current_user.payments.filter(promo_code=promo_code).count() > 0:
                    return False
                if promo_code.only_user_id and promo_code.only_user_id != current_user.user_id:
                    return False
            if promo_code.only_period and new_duration and promo_code.only_period != new_duration:
                return False
            if promo_code.only_plan and new_plan and promo_code.only_plan != new_plan:
                return False
            return promo_code
        except cls.DoesNotExist:
            return False

    @classmethod
    def create_education_promo_code(cls, **data):
        # The promo code will be expired in one year
        expired_time = int(now() + 365 * 86400)
        value = 100
        code = f"{EDUCATION_PROMO_PREFIX}{random_n_digit(n=12)}".upper()
        only_user_id = data.get("user_id")
        promo_code_data = {
            "type": PROMO_PERCENTAGE,
            "expired_time": expired_time,
            "code": code,
            "value": value,
            "duration": 1,
            "number_code": 1,
            "description_en": "Locker PromoCode Reward",
            "description_vi": "Locker PromoCode Reward",
            "only_user_id": only_user_id,
            "only_period": DURATION_YEARLY,
            "only_plan": PLAN_TYPE_PM_PREMIUM,
        }
        promo_code_obj = PromoCode.create(**promo_code_data)

        # Create on Stripe
        if os.getenv("PROD_ENV") in ["prod", "staging"]:
            try:
                stripe.Coupon.create(
                    duration='once',
                    id="{}_yearly".format(promo_code_obj.id),
                    percent_off=value,
                    name=code,
                    redeem_by=expired_time
                )
            except stripe.error.StripeError:
                promo_code_obj.delete()
                return None
        return promo_code_obj

    def get_discount(self, total_price, duration=DURATION_MONTHLY):
        discount = 0
        # Get discount by promo type
        if self.type.name == PROMO_AMOUNT:
            discount = float(self.value)
        elif self.type.name == PROMO_PERCENTAGE:
            discount = round(float(self.value * total_price / 100), 2)
        # Check limit value
        if self.limit_value and (discount > self.limit_value):
            discount = self.limit_value

        discount = min(discount, total_price)
        return discount

    def get_number_applied_period(self, duration=DURATION_MONTHLY):
        if not self.specific_duration:
            return self.duration
        if duration == DURATION_YEARLY:
            months = 12
        elif duration == DURATION_HALF_YEARLY:
            months = 6
        else:
            months = 1
        return math.ceil(self.duration/months)


