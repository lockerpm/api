from locker_server.core.exceptions.app import CoreException


class BackupCredentialException(CoreException):
    """
    Base exception
    """


class BackupCredentialDoesNotExistException(BackupCredentialException):
    """
    The BackupCredential does not exist
    """


class BackupCredentialMaximumReachedException(BackupCredentialException):
    """
    The maximum number of items is reached"
    """
