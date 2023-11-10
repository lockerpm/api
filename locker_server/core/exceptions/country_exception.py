from locker_server.core.exceptions.app import CoreException


class CountryException(CoreException):
    """
    Base exception
    """


class CountryDoesNotExistException(CountryException):
    """
    The Country does not exist (not found country code, country name,...)
    """
