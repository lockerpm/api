from locker_server.core.exceptions.app import CoreException


class EmergencyAccessException(CoreException):
    """
    Base EmergencyAccess Exception
    """


class EmergencyAccessDoesNotExistException(EmergencyAccessException):
    """
    The EmergencyAccess does not exist
    """


class EmergencyAccessGranteeExistedException(EmergencyAccessException):
    """
    The grantee existed
    """


class EmergencyAccessEmailExistedException(EmergencyAccessException):
    """
    The emergency access email existed
    """