from typing import Optional, List, Dict
from abc import ABC, abstractmethod

from locker_server.core.entities.payment.payment import Payment
from locker_server.core.entities.payment.promo_code import PromoCode


class PaymentRepository(ABC):
    # ------------------------ List Payment resource ------------------- #
    @abstractmethod
    def list_all_invoices(self, **filter_params) -> List[Payment]:
        pass

    @abstractmethod
    def list_invoices_by_user(self, user_id: int, **filter_params) -> List[Payment]:
        pass

    @abstractmethod
    def list_feedback_after_subscription(self, after_days: int = 30) -> List[Dict]:
        pass

    # ------------------------ Get Payment resource --------------------- #
    @abstractmethod
    def is_blocked_by_source(self, user_id: int, utm_source: str) -> bool:
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int, payment_id: str) -> Optional[Payment]:
        pass

    @abstractmethod
    def get_by_payment_id(self, payment_id: str) -> Optional[Payment]:
        pass

    @abstractmethod
    def get_by_mobile_invoice_id(self, mobile_invoice_id: str) -> Optional[Payment]:
        pass

    @abstractmethod
    def get_by_stripe_invoice_id(self, stripe_invoice_id: str) -> Optional[Payment]:
        pass

    @abstractmethod
    def get_by_banking_code(self, code: str) -> Optional[Payment]:
        pass

    @abstractmethod
    def check_saas_promo_code(self, user_id: int, code: str) -> Optional[PromoCode]:
        pass

    @abstractmethod
    def check_promo_code(self, user_id: int, code: str, new_duration: str = None, new_plan: str = None) -> Optional[PromoCode]:
        pass

    @abstractmethod
    def count_referral_payments(self, referral_user_ids: List[int]) -> int:
        pass

    # ------------------------ Create Payment resource --------------------- #
    @abstractmethod
    def create_payment(self, **payment_data) -> Optional[Payment]:
        pass

    @abstractmethod
    def create_education_promo_code(self, user_id: int) -> Optional[PromoCode]:
        pass

    # ------------------------ Update Payment resource --------------------- #
    @abstractmethod
    def update_promo_code_remaining_times(self, promo_code: PromoCode, amount: int = 1) -> PromoCode:
        pass

    @abstractmethod
    def update_payment(self, payment: Payment, update_data) -> Payment:
        pass

    @abstractmethod
    def set_paid(self, payment: Payment) -> Payment:
        pass

    @abstractmethod
    def set_past_due(self, payment: Payment, failure_reason=None) -> Payment:
        pass

    @abstractmethod
    def set_failed(self, payment: Payment, failure_reason=None) -> Payment:
        pass

    # ------------------------ Delete Payment resource --------------------- #

