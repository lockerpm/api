from locker_server.core.entities.payment.promo_code_type import PromoCodeType
from locker_server.core.entities.payment.saas_market import SaasMarket
from locker_server.core.entities.user.user import User
from locker_server.shared.constants.transactions import CURRENCY_USD


class PromoCode(object):
    def __init__(self, promo_code_id: str, created_time: float = None, expired_time: float = None,
                 remaining_times: int = 0, valid: bool = True, code: str = None, value: float = 0,
                 limit_value: float = None, duration: int = 1, specific_duration: str = None,
                 currency: str = CURRENCY_USD, description_en: str = "", description_vi: str = "",
                 promo_code_type: PromoCodeType = None,
                 is_saas_code: bool = False, saas_market: SaasMarket = None, saas_plan: str = None,
                 only_user: User = None, only_period: str = None):
        self._promo_code_id = promo_code_id
        self._created_time = created_time
        self._expired_time = expired_time
        self._remaining_times = remaining_times
        self._valid = valid
        self._code = code
        self._value = value
        self._limit_value = limit_value
        self._duration = duration
        self._specific_duration = specific_duration
        self._currency = currency
        self._description_en = description_en
        self._description_vi = description_vi
        self._promo_code_type = promo_code_type
        self._is_saas_code = is_saas_code
        self._saas_market = saas_market
        self._saas_plan = saas_plan
        self._only_user = only_user
        self._only_period = only_period

    @property
    def promo_code_id(self):
        return self._promo_code_id

    @property
    def created_time(self):
        return self._created_time

    @property
    def expired_time(self):
        return self._expired_time

    @property
    def remaining_times(self):
        return self._remaining_times

    @property
    def valid(self):
        return self._valid

    @property
    def code(self):
        return self._code

    @property
    def value(self):
        return self._value

    @property
    def limit_value(self):
        return self._limit_value

    @property
    def duration(self):
        return self._duration

    @property
    def specific_duration(self):
        return self._specific_duration

    @property
    def currency(self):
        return self._currency

    @property
    def description_vi(self):
        return self._description_vi

    @property
    def description_en(self):
        return self._description_en

    @property
    def promo_code_type(self):
        return self._promo_code_type

    @property
    def is_saas_code(self):
        return self._is_saas_code

    @property
    def saas_market(self):
        return self._saas_market

    @property
    def saas_plan(self):
        return self._saas_plan

    @property
    def only_user(self):
        return self._only_user

    @property
    def only_period(self):
        return self._only_period
