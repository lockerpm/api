from shared.constants.transactions import PAYMENT_METHOD_CARD, PAYMENT_METHOD_WALLET, PAYMENT_METHOD_BANKING
from cystack_models.factory.payment_method.stripe_method import StripePaymentMethod
from cystack_models.factory.payment_method.wallet_method import WalletPaymentMethod
from cystack_models.factory.payment_method.banking_method import BankingPaymentMethod


class PaymentMethodFactory:
    @classmethod
    def get_method(cls, user, scope, payment_method: str):
        if payment_method == PAYMENT_METHOD_CARD:
            return StripePaymentMethod(user=user, scope=scope)
        elif payment_method == PAYMENT_METHOD_WALLET:
            return WalletPaymentMethod(user=user, scope=scope)
        elif payment_method == PAYMENT_METHOD_BANKING:
            return BankingPaymentMethod(user=user, scope=scope)
        raise PaymentMethodNotSupportException(payment_method=payment_method)


class PaymentMethodNotSupportException(BaseException):
    """

    """

    def __init__(self, payment_method, message="Destination device mismatched"):
        message = "Payment method {} is not supported".format(payment_method) if payment_method else message
        super(PaymentMethodNotSupportException, self).__init__(message)
        self._payment_method = payment_method

    @property
    def payment_method(self):
        return self._payment_method
