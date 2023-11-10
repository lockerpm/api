from locker_server.core.exceptions.app import CoreException


class DeviceException(CoreException):
    """
    Base Device Exception
    """


class DeviceDoesNotExistException(DeviceException):
    """
    The device does not exist
    """
