from locker_server.core.exceptions.app import CoreException


class TeamMemberException(CoreException):
    """
    Base exception
    """


class TeamMemberDoesNotExistException(TeamMemberException):
    """
    The TeamMember does not exist
    """


class TeamMemberEmailDoesNotExistException(TeamMemberException):
    """
    Member email does not exist
    """


class OnlyAllowOwnerUpdateException(TeamMemberException):
    """

    """


class OwnerDoesNotExistException(TeamMemberException):
    """
    The Owner does not exist in team
    """
