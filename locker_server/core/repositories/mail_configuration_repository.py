from typing import Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.configuration.mail_configuration import MailConfiguration


class MailConfigurationRepository(ABC):
    # ------------------------ List MailConfiguration resource ------------------- #

    # ------------------------ Get MailConfiguration resource --------------------- #
    @abstractmethod
    def get_mail_configuration(self) -> Optional[MailConfiguration]:
        pass

    # ------------------------ Create MailConfiguration resource --------------------- #

    # ------------------------ Update MailConfiguration resource --------------------- #
    @abstractmethod
    def update_mail_configuration(self, mail_config_data) -> MailConfiguration:
        pass

    # ------------------------ Delete MailConfiguration resource --------------------- #
    @abstractmethod
    def destroy_mail_configuration(self):
        pass
