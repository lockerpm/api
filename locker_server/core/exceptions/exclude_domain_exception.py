from locker_server.core.exceptions.app import CoreException


class ExcludeDomainException(CoreException):
    """
    Base ExcludeDomain Exception
    """


class ExcludeDomainNotExistException(ExcludeDomainException):
    """
    The ExcludeDomain does not exist
    """
