from locker_server.core.exceptions.app import CoreException


class PlanException(CoreException):
    """
    Base exception
    """


class PlanDoesNotExistException(PlanException):
    """
    The plan does not exist
    """