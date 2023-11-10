from locker_server.core.exceptions.app import CoreException


class UserRewardMissionException(CoreException):
    """
    Base exception
    """


class UserRewardMissionDoesNotExistException(UserRewardMissionException):
    """
    The UserRewardMission does not exist (not found id, etc...)
    """


class UserRewardPromoCodeInvalidException(UserRewardMissionException):
    """
    The available promo code value is not valid
    """
