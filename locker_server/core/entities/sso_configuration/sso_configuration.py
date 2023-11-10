from locker_server.core.entities.sso_configuration.sso_provider import SSOProvider
from locker_server.core.entities.user.user import User


class SSOConfiguration(object):
    def __init__(self, sso_configuration_id: str, created_by: User, sso_provider: SSOProvider, identifier: str,
                 enabled: bool, sso_provider_options: str = "", creation_date: float = 0, revision_date: float = 0):
        self._sso_configuration_id = sso_configuration_id
        self._created_by = created_by
        self._sso_provider = sso_provider
        self._identifier = identifier
        self._creation_date = creation_date
        self._revision_date = revision_date
        self._sso_provider_options = sso_provider_options
        self._enabled = enabled

    @property
    def sso_configuration_id(self):
        return self._sso_configuration_id

    @property
    def created_by(self):
        return self._created_by

    @property
    def sso_provider(self):
        return self._sso_provider

    @property
    def sso_provider_options(self):
        return self._sso_provider_options

    @property
    def enabled(self):
        return self._enabled

    @property
    def identifier(self):
        return self._identifier

    @property
    def creation_date(self):
        return self._creation_date

    @property
    def revision_date(self):
        return self._revision_date
