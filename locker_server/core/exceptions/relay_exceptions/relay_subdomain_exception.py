from locker_server.core.exceptions.app import CoreException


class RelaySubdomainException(CoreException):
    """
    Base exception
    """


class RelaySubdomainDoesNotExistException(RelaySubdomainException):
    """
    The RelaySubdomain does not exist
    """


class MaxRelaySubdomainReachedException(RelaySubdomainException):
    """
    The number of RelaySubdomain is reached
    """


class RelaySubdomainExistedException(RelaySubdomainException):
    """
    The subdomain already existed
    """


class RelaySubdomainInvalidException(RelaySubdomainException):
    """
    The subdomain is not valid (has black words, blocked words, etc...)
    """


class RelaySubdomainAlreadyUsedException(RelaySubdomainException):
    """
    The subdomain is used
    """
