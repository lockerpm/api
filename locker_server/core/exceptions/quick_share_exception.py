from locker_server.core.exceptions.app import CoreException


class QuickShareException(CoreException):
    """
    Base exception
    """


class QuickShareDoesNotExistException(QuickShareException):
    """
    The QuickShare does not exist
    """


class QuickShareNotValidAccessException(QuickShareException):
    """

    """


class QuickShareRequireOTPException(QuickShareException):
    """
    The QuickShare is required OTP
    """