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
        raise Exception('Payment method {} is not supported'.format(payment_method))
