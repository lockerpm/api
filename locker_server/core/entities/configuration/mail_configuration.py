from locker_server.core.entities.configuration.mail_provider import MailProvider


class MailConfiguration(object):
    def __init__(self, mail_provider: MailProvider, mail_provider_options="",
                 sending_domain: str = None, from_email: str = None, from_name: str = None):
        self._mail_provider = mail_provider
        self._mail_provider_options = mail_provider_options or {}
        self._sending_domain = sending_domain
        self._from_email = from_email
        self._from_name = from_name

    @property
    def mail_provider(self):
        return self._mail_provider

    @property
    def mail_provider_options(self):
        return self._mail_provider_options

    @property
    def sending_domain(self):
        return self._sending_domain

    @property
    def from_email(self):
        return self._from_email

    @property
    def from_name(self):
        return self._from_name

    def to_json(self):
        return {
            "mail_provider": self.mail_provider.mail_provider_id,
            "sending_domain": self.sending_domain,
            "from_email": self.from_email,
            "from_name": self.from_name,
            "mail_provider_options": self.mail_provider_options
        }
