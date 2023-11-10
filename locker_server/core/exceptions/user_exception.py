from locker_server.core.exceptions.app import CoreException


class UserException(CoreException):
    """
    Base exception
    """


class UserDoesNotExistException(UserException):
    """
    The User does not exist (not found id or not found username, etc...)
    """


class UserPasswordInvalidException(UserException):
    """
    The password is not invalid
    """


class UserAuthFailedException(UserException):
    """
    The User device access token is not valid
    """


class UserAuthFailedPasswordlessRequiredException(UserAuthFailedException):
    """

    """


class UserCreationDeniedException(UserException):
    """
    The admin user is created. So users can not create new one for enterprise plan.
    """


class UserResetPasswordTokenInvalidException(UserException):
    """
    The reset password token expired
    """


class UserAuthBlockingEnterprisePolicyException(UserAuthFailedException):
    def __init__(self, wait, message="Login locked due to the enterprise's policy"):
        super().__init__(message)
        self._wait = wait

    @property
    def wait(self):
        return self._wait


class UserAuthBlockedEnterprisePolicyException(UserAuthFailedException):
    def __init__(self,
                 failed_login_owner_email: bool = False,
                 owner: int = None,
                 lock_time: str = None,
                 unlock_time: str = None,
                 ip: str = None,
                 message="The next login will be locked due to the enterprise's policy"):
        super().__init__(message)
        self._failed_login_owner_email = failed_login_owner_email
        self._owner = owner
        self._lock_time = lock_time
        self._unlock_time = unlock_time
        self._ip = ip

    @property
    def failed_login_owner_email(self):
        return self._failed_login_owner_email

    @property
    def owner(self):
        return self._owner

    @property
    def lock_time(self):
        return self._lock_time

    @property
    def unlock_time(self):
        return self._unlock_time

    @property
    def ip(self):
        return self._ip


class UserIsLockedByEnterpriseException(UserException):
    """
    The account is locked by the Enterprise Admin
    """


class UserEnterprisePlanExpiredException(UserException):
    """
    The account is locked because the enterprise plan is expired
    """


class UserBelongEnterpriseException(UserException):
    """
    The account belongs to the Enterprise
    """


class User2FARequireException(UserException):
    """
    The enterprise policy requires 2FA
    """
