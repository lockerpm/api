from locker_server.core.exceptions.app import CoreException


class PaymentException(CoreException):
    """
    Payment base exception
    """


class PaymentMethodNotSupportException(PaymentException):
    """

    """

    def __init__(self, payment_method, message="Payment method is not support"):
        message = "Payment method {} is not supported".format(payment_method) if payment_method else message
        super(PaymentMethodNotSupportException, self).__init__(message)
        self._payment_method = payment_method

    @property
    def payment_method(self):
        return self._payment_method


class PaymentInvoiceDoesNotExistException(PaymentException):
    """
    The payment does not exist
    """


class PaymentPromoCodeInvalidException(PaymentException):
    """
    The promo code is invalid
    """


class PaymentNotFoundCardException(PaymentException):
    """
    The user does not any card
    """


class PaymentFailedByUserInFamilyException(PaymentException):
    """
    The payment is failed because user is in other family plan
    """


class PaymentFailedByUserInLifetimeException(PaymentException):
    """
    The payment is failed because user is in Lifetime plan
    """


class CurrentPlanDoesNotSupportOperatorException(PaymentException):
    """
    The current plan does not support the operator
    """


class EducationEmailClaimedException(PaymentException):
    """
    The education email is claimed
    """


class EducationEmailInvalidException(PaymentException):
    """
    The education email is not valid
    """


class CreateEducationEmailPromoCodeFailedException(PaymentException):
    """
    Create education promo code failed
    """


class UpgradePlanNotChangeException(PaymentException):
    """
    Plan does not change
    """


class UpgradePaymentMethodChangedException(PaymentException):
    """

    """


class MaxFamilyMemberReachedException(PaymentException):
    """

    """


class CannotCancelDefaultPlanException(PaymentException):
    """

    """


class CurrentPlanIsEnterpriseException(PaymentException):
    """
    The current plan is Enterprise
    """