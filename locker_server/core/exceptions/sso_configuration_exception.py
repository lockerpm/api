from locker_server.core.exceptions.app import CoreException


class OrganizationSSOConfigurationException(CoreException):
    """
    Base exception
    """


class SSOConfigurationDoesNotExistException(OrganizationSSOConfigurationException):
    """
    The sso configuration does not exist
    """


class SSOConfigurationIdentifierExistedException(OrganizationSSOConfigurationException):
    """
    The identifier already existed
    """
