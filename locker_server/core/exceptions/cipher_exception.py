from locker_server.core.exceptions.app import CoreException


class CipherException(CoreException):
    """
    Base exception
    """


class CipherDoesNotExistException(CipherException):
    """
    The Cipher does not exist
    """


class FolderDoesNotExistException(CipherException):
    """
    The Folder does not exist
    """


class CipherMaximumReachedException(CipherException):
    """
    The maximum number of items is reached. Please check your trash if any"
    """


class CipherBelongCollectionException(CipherException):
    """
    The cipher belongs to a Collection
    """


class CipherBelongTeamException(CipherException):
    """
    This item already belongs to an organization
    """


class StopCipherEmptyException(CipherException):
    """
    Not allow the stop cipher empty
    """