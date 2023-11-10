class SSOProvider(object):
    def __init__(self, sso_provider_id: str, name: str):
        self._sso_provider_id = sso_provider_id
        self._name = name

    @property
    def sso_provider_id(self):
        return self._sso_provider_id

    @property
    def name(self):
        return self._name
