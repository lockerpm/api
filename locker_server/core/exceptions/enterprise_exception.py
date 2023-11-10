from locker_server.core.exceptions.app import CoreException


class EnterpriseException(CoreException):
    """
    Base exception
    """


class EnterpriseDoesNotExistException(EnterpriseException):
    """
    The enterprise does not exist
    """
