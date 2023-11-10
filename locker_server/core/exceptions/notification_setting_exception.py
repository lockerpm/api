from locker_server.core.exceptions.app import CoreException


class NotificationSettingException(CoreException):
    """
    Base exception
    """


class NotificationSettingDoesNotExistException(NotificationSettingException):
    """
    The NotificationSetting does not exist (not found id)
    """
