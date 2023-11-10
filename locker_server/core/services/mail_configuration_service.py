from typing import Optional

from locker_server.core.entities.configuration.mail_configuration import MailConfiguration
from locker_server.core.repositories.mail_configuration_repository import MailConfigurationRepository


class MailConfigurationService:
    def __init__(self, mail_configuration_repository: MailConfigurationRepository):
        self.mail_configuration_repository = mail_configuration_repository

    def get_mail_configuration(self) -> Optional[MailConfiguration]:
        return self.mail_configuration_repository.get_mail_configuration()

    def update_mail_configuration(self, mail_config_data) -> MailConfiguration:
        return self.mail_configuration_repository.update_mail_configuration(
            mail_config_data=mail_config_data
        )

    def destroy_mail_configuration(self):
        return self.mail_configuration_repository.destroy_mail_configuration()
