from locker_server.core.exceptions.app import CoreException


class UserPlanException(CoreException):
    """
    Base exception
    """


class MaxUserPlanFamilyReachedException(UserPlanException):
    """
    Max family member is reached
    """


class UserIsInOtherFamilyException(UserPlanException):
    """
    The user is in other family plan
    """

    def __init__(self, email=None, message="The user is in other family plan"):
        message = "The user {} is in other family pla".format(email) if email else message
        super().__init__(message)
        self._email = email

    @property
    def email(self):
        return self._email


class UserPlanFamilyDoesNotExistException(UserPlanException):
    """
    The user plan family does not exist
    """


class EnterpriseTrialCodeInvalidException(UserPlanException):
    """
    The trial code is invalid for the trial enterprise plan
    """


class EnterpriseTrialAppliedException(UserPlanException):
    """
    The trial of the enterprise is applied
    """