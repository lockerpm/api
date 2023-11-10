from locker_server.api_orm.models import *
from locker_server.core.entities.configuration.mail_configuration import MailConfiguration
from locker_server.core.entities.configuration.mail_provider import MailProvider


class ConfigurationParser:
    @classmethod
    def parse_mail_provider(cls, mail_provider_orm: MailProviderORM) -> MailProvider:
        return MailProvider(
            mail_provider_id=mail_provider_orm.id, name=mail_provider_orm.name, available=mail_provider_orm.available
        )

    @classmethod
    def parse_mail_configuration(cls, mail_configuration_orm: MailConfigurationORM) -> MailConfiguration:
        return MailConfiguration(
            mail_provider=cls.parse_mail_provider(mail_provider_orm=mail_configuration_orm.mail_provider),
            mail_provider_options=mail_configuration_orm.get_mail_provider_option(),
            sending_domain=mail_configuration_orm.sending_domain,
            from_email=mail_configuration_orm.from_email,
            from_name=mail_configuration_orm.from_name,
        )
