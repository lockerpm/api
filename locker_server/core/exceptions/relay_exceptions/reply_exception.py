from locker_server.core.exceptions.app import CoreException


class ReplyException(CoreException):
    """
    Base exception
    """


class ReplyDoesNotExistException(ReplyException):
    """
    The Reply does not exist
    """


class ReplyLookupExistedException(ReplyException):
    """
    The Reply with lookup already existed
    """
