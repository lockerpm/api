from abc import ABC, abstractmethod

from cystack_models.models.users.users import User
from cystack_models.models.payments.payments import Payment


class IPaymentRepository(ABC):
    @abstractmethod
    def get_invoice_by_id(self, invoice_id: str) -> Payment:
        pass

    @abstractmethod
    def get_invoice_by_user(self, user: User, invoice_id: str) -> Payment:
        pass

    @abstractmethod
    def get_list_invoices_by_user(self, user: User):
        pass

    @abstractmethod
    def set_paid(self, payment: Payment):
        pass

    @abstractmethod
    def set_past_due(self, payment: Payment, failure_reason=None):
        pass

    @abstractmethod
    def set_failed(self, payment: Payment, failure_reason=None):
        pass

    @abstractmethod
    def set_processing(self, payment: Payment):
        pass

    @abstractmethod
    def pending_cancel(self, payment: Payment):
        pass

    @abstractmethod
    def retry(self, payment: Payment):
        pass
