import math
import uuid

from django.db import models

from shared.constants.transactions import *
from shared.utils.app import now
from cystack_models.models.payments.promo_code_types import PromoCodeType
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
    currency = models.CharField(max_length=8, default=CURRENCY_USD)
    description_en = models.TextField(default="", blank=True)
    description_vi = models.TextField(default="", blank=True)
    only_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="only_promo_codes", null=True)
    only_period = models.CharField(max_length=128, null=True, default=None)
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

        new_promo_code = cls(
            created_time=now(), expired_time=expired_time, remaining_times=number_code, code=code,
            value=value, limit_value=limit_value, currency=currency,
            type=PromoCodeType.objects.get(name=promo_type),
            duration=duration, specific_duration=specific_duration,
            description_vi=description_vi, description_en=description_en,
            only_user_id=only_user_id
        )
        new_promo_code.save()
        return new_promo_code

    @classmethod
    def check_valid(cls, value, current_user, new_duration: str = None):
        """
        Check a promo code value is valid
        :param value:
        :param current_user:
        :param new_duration:
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
            return promo_code
        except cls.DoesNotExist:
            return False

    @classmethod
    def check_saas_valid(cls, value, current_user):
        try:
            promo_code = cls.objects.get(code=value, valid=True)
            # If promo code was expired or promo code was used by this user?
            if promo_code.expired_time < now() or promo_code.remaining_times <= 0 or promo_code.is_saas_code is False:
                return False
            if current_user is not None and current_user.payments.filter(promo_code=promo_code).count() > 0:
                return False
            return promo_code
        except cls.DoesNotExist:
            return False

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


