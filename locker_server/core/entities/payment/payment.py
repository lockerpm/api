from datetime import datetime

from locker_server.core.entities.payment.customer import Customer
from locker_server.core.entities.payment.promo_code import PromoCode
from locker_server.core.entities.user.user import User
from locker_server.shared.constants.transactions import CURRENCY_USD, TRANSACTION_TYPE_PAYMENT, DURATION_MONTHLY, \
    DURATION_YEARLY, DURATION_HALF_YEARLY


class Payment(object):
    def __init__(self, id: int, payment_id: str, created_time: float = None, total_price: float = 0,
                 discount: float = 0, currency: str = CURRENCY_USD, status: str = None, description: str = "",
                 transaction_type: str = TRANSACTION_TYPE_PAYMENT, payment_method: str = None,
                 failure_reason: str = None, stripe_invoice_id: str = None, mobile_invoice_id: str = None,
                 code: str = None, bank_id: int = None, scope: str = None, plan: str = None,
                 duration: str = DURATION_MONTHLY, metadata: str = None, enterprise_id: str = None, user: User = None,
                 promo_code: PromoCode = None, customer: Customer = None):
        self._id = id
        self._payment_id = payment_id
        self._created_time = created_time
        self._total_price = total_price
        self._discount = discount
        self._currency = currency
        self._status = status
        self._description = description
        self._transaction_type = transaction_type
        self._payment_method = payment_method
        self._failure_reason = failure_reason
        self._stripe_invoice_id = stripe_invoice_id
        self._mobile_invoice_id = mobile_invoice_id
        self._code = code
        self._bank_id = bank_id
        self._scope = scope
        self._plan = plan
        self._duration = duration
        self._metadata = metadata
        self._enterprise_id = enterprise_id
        self._user = user
        self._promo_code = promo_code
        self._customer = customer

    @property
    def id(self):
        return self._id

    @property
    def payment_id(self):
        return self._payment_id

    @property
    def created_time(self):
        return self._created_time

    @property
    def total_price(self):
        return self._total_price

    @property
    def discount(self):
        return self._discount

    @property
    def currency(self):
        return self._currency

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status_value):
        self._status = status_value

    @property
    def description(self):
        return self._description

    @property
    def transaction_type(self):
        return self._transaction_type

    @property
    def payment_method(self):
        return self._payment_method

    @property
    def failure_reason(self):
        return self._failure_reason

    @failure_reason.setter
    def failure_reason(self, failure_reason_value):
        self._failure_reason = failure_reason_value

    @property
    def stripe_invoice_id(self):
        return self._stripe_invoice_id

    @property
    def mobile_invoice_id(self):
        return self._mobile_invoice_id

    @property
    def code(self):
        return self._code

    @property
    def bank_id(self):
        return self._bank_id

    @property
    def scope(self):
        return self._scope

    @property
    def plan(self):
        return self._plan

    @property
    def duration(self):
        return self._duration

    @property
    def metadata(self):
        return self._metadata

    @property
    def enterprise_id(self):
        return self._enterprise_id

    @property
    def user(self):
        return self._user

    @property
    def promo_code(self):
        return self._promo_code

    @property
    def customer(self):
        return self._customer

    def get_created_time_str(self):
        return datetime.utcfromtimestamp(self.created_time).strftime('%H:%M:%S %d-%m-%Y') if self.created_time else None

    def get_customer_dict(self):
        if not self.customer:
            return {}
        return {
            "full_name": self.customer.full_name,
            "organization": self.customer.organization,
            "address": self.customer.address,
            "city": self.customer.city,
            "state": self.customer.state,
            "postal_code": self.customer.postal_code,
            "phone_number": self.customer.phone_number,
            "last4": self.customer.last4,
            "brand": self.customer.brand,
            "country": "" if not self.customer.country else self.customer.country.country_name
        }

    @classmethod
    def get_duration_month_number(cls, duration):
        if duration == DURATION_YEARLY:
            return 12
        elif duration == DURATION_HALF_YEARLY:
            return 6
        return 1
