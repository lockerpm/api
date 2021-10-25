import stripe

from core.repositories import IPaymentRepository

from shared.constants.transactions import *
from cystack_models.models.payments.payments import Payment
from cystack_models.models.users.users import User


class PaymentRepository(IPaymentRepository):
    def get_invoice_by_id(self, invoice_id: str) -> Payment:
        return Payment.objects.get(payment_id=invoice_id)

    def get_invoice_by_user(self, user: User, invoice_id: str) -> Payment:
        return Payment.objects.get(payment_id=invoice_id, user=user)

    def get_list_invoices_by_user(self, user: User):
        return Payment.objects.filter(user=user)

    def set_paid(self, payment: Payment):
        payment.status = PAYMENT_STATUS_PAID
        payment.save()
        return payment

    def set_past_due(self, payment: Payment, failure_reason=None):
        payment.failure_reason = failure_reason
        payment.status = PAYMENT_STATUS_PAST_DUE
        payment.save()
        return payment

    def set_failed(self, payment: Payment, failure_reason=None):
        payment.failure_reason = failure_reason
        payment.status = PAYMENT_STATUS_FAILED
        payment.save()
        return payment

    def set_processing(self, payment: Payment):
        payment.status = PAYMENT_STATUS_PROCESSING
        payment.save()
        return payment

    def pending_cancel(self, payment: Payment):
        payment.delete()

    def retry(self, payment: Payment):
        if payment.stripe_invoice_id is not None:
            invoice = stripe.Invoice.retrieve(payment.stripe_invoice_id)
            invoice.pay()
        return payment

