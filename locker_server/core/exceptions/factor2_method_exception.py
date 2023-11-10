from locker_server.core.exceptions.app import CoreException


class Factor2MethodException(CoreException):
    """
    Base exception
    """


class Factor2MethodDoesNotExistException(Factor2MethodException):
    """
    The Factor2Method does not exist
    """


class Factor2MethodInvalidException(Factor2MethodException):
    """
    The Method invalid
    """


class Factor2CodeInvalidException(Factor2MethodException):
    """
    The otp code invalid
    """
