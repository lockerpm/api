from locker_server.core.exceptions.app import CoreException


class EnterpriseGroupException(CoreException):
    """
    Base exception
    """


class EnterpriseGroupDoesNotExistException(EnterpriseGroupException):
    """
    The enterprise group does not exist
    """
