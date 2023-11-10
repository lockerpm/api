import math
import uuid

from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.constants.transactions import CURRENCY_USD, PROMO_AMOUNT, PROMO_PERCENTAGE, DURATION_MONTHLY
from locker_server.shared.utils.app import now


class AbstractPromoCodeORM(models.Model):
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
    currency = models.CharField(max_length=8, default=CURRENCY_USD)
    description_en = models.TextField(default="", blank=True)
    description_vi = models.TextField(default="", blank=True)

    type = models.ForeignKey(
        locker_server_settings.LS_PROMO_CODE_TYPE_MODEL, on_delete=models.CASCADE, related_name="promo_codes"
    )

    class Meta:
        abstract = True

    @classmethod
    def create(cls, **data):
        raise NotImplementedError

    @classmethod
    def check_valid(cls, value, current_user, new_duration: str = None, new_plan: str = None):
        raise NotImplementedError

    @classmethod
    def check_saas_valid(cls, value, current_user):
        raise NotImplementedError

    def get_discount(self, total_price: float, duration: str = DURATION_MONTHLY):
        raise NotImplementedError
    #
    # def get_number_applied_period(self, duration=DURATION_MONTHLY):
    #     if not self.specific_duration:
    #         return self.duration
    #     if duration == DURATION_YEARLY:
    #         months = 12
    #     elif duration == DURATION_HALF_YEARLY:
    #         months = 6
    #     else:
    #         months = 1
    #     return math.ceil(self.duration/months)
