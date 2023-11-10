from locker_server.core.exceptions.app import CoreException


class EnterpriseMemberException(CoreException):
    """
    Base exception
    """


class EnterpriseMemberDoesNotExistException(EnterpriseMemberException):
    """
    The enterprise member does not exist
    """


class EnterpriseMemberPrimaryDoesNotExistException(EnterpriseMemberException):
    """
    The enterprise member primary doest not exist
    """


class EnterpriseMemberUpdatedFailedException(EnterpriseMemberException):
    """
    The enterprise member can not be updated: updated primary member or update yourself
    """


class EnterpriseMemberInvitationUpdatedFailedException(EnterpriseMemberException):
    """
    Then invitation enterprise member can not reject
    """
