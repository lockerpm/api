from locker_server.core.exceptions.app import CoreException


class RelayAddressException(CoreException):
    """
    Base exception
    """


class RelayAddressDoesNotExistException(RelayAddressException):
    """
    The RelayAddress does not exist
    """


class RelayAddressReachedException(RelayAddressException):
    """
    The number of RelayAddress is reached
    """


class RelayAddressInvalidException(RelayAddressException):
    """The address have invalid word"""


class RelayAddressUpdateDeniedException(RelayAddressException):
    """
    The RelayAddress is not oldest
    """


class RelayAddressExistedException(RelayAddressException):
    """
    The address already exist
    """
