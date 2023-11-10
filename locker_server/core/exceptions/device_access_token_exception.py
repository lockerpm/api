from locker_server.core.exceptions.app import CoreException


class DeviceAccessTokenException(CoreException):
    """
    Base exception
    """


class DeviceAccessTokenDoesNotExistException(DeviceAccessTokenException):
    """
    The device access token does not exist
    """
