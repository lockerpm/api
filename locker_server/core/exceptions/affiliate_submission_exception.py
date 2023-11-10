from locker_server.core.exceptions.app import CoreException


class AffiliateSubmissionException(CoreException):
    """
    Base exception
    """


class AffiliateSubmissionDoesNotExistException(AffiliateSubmissionException):
    """
    The AffiliateSubmission does not exist (not found id)
    """
