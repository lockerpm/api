class MailProvider(object):
    def __init__(self, mail_provider_id: str, name: str, available: bool = True):
        self._mail_provider_id = mail_provider_id
        self._name = name
        self._available = available

    @property
    def mail_provider_id(self):
        return self._mail_provider_id

    @property
    def name(self):
        return self._name

    @property
    def available(self):
        return self._available
