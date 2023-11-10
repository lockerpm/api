from locker_server.core.exceptions.app import CoreException


class EnterpriseMemberException(CoreException):
    """
    Base exception
    """


class EnterpriseMemberDoesNotExistException(EnterpriseMemberException):
    """

    """


class EnterpriseMemberExistedException(EnterpriseMemberException):
    """

    """