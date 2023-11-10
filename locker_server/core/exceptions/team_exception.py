from locker_server.core.exceptions.app import CoreException


class TeamException(CoreException):
    """
    Base exception
    """


class TeamDoesNotExistException(TeamException):
    """
    The Team does not exist
    """


class TeamLockedException(TeamException):
    """
    The Team is locked
    """


class TeamGroupDoesNotExistException(TeamException):
    """
    The sharing group does not exist
    """