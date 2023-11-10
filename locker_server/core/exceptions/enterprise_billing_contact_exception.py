from locker_server.core.exceptions.app import CoreException


class EnterpriseBillingContactException(CoreException):
    """
    Base exception
    """


class EnterpriseBillingContactDoesNotExistException(EnterpriseBillingContactException):
    """
    The EnterpriseBillingContact does not exist
    """
