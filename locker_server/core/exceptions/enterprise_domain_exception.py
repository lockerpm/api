from locker_server.core.exceptions.app import CoreException


class DomainException(CoreException):
    """
    Base exception
    """


class DomainDoesNotExistException(DomainException):
    """
    The Domain does not exist
    """


class DomainExistedException(DomainException):
    """
    The Domain already existed
    """


class DomainVerifiedByOtherException(DomainException):
    """
    The Domain is verified by other
    """


class DomainVerifiedErrorException(DomainException):
    """
    The Domain ownership is not verified
    """
