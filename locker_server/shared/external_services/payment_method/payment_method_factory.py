from locker_server.core.exceptions.payment_exception import PaymentMethodNotSupportException
from locker_server.shared.constants.transactions import PAYMENT_METHOD_CARD, PAYMENT_METHOD_WALLET
from locker_server.shared.external_services.payment_method.impl.stripe_method import StripePaymentMethod
from locker_server.shared.external_services.payment_method.impl.wallet_method import WalletPaymentMethod
from locker_server.shared.external_services.payment_method.payment_method import PaymentMethod


class PaymentMethodFactory:
    @classmethod
    def get_method(cls, user_plan: object, scope: str, payment_method: str) -> PaymentMethod:
        if payment_method == PAYMENT_METHOD_CARD:
            return StripePaymentMethod(user_plan=user_plan, scope=scope)
        elif payment_method == PAYMENT_METHOD_WALLET:
            return WalletPaymentMethod(user_plan=user_plan, scope=scope)
        raise PaymentMethodNotSupportException(payment_method=payment_method)
