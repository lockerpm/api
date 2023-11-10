from locker_server.core.exceptions.app import CoreException


class NotificationException(CoreException):
    """
    Base exception
    """


class NotificationDoesNotExistException(NotificationException):
    """
    The Notification does not exist
    """
