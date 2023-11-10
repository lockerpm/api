from locker_server.core.exceptions.app import CoreException


class EnterprisePolicyException(CoreException):
    """
    Base exception
    """


class EnterprisePolicyDoesNotExistException(EnterprisePolicyException):
    """
    The EnterprisePolicy does not exist
    """
