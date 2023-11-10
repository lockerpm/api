from abc import ABC, abstractmethod
from typing import List

from locker_server.core.entities.configuration.mail_provider import MailProvider


class MailProviderRepository(ABC):
    @abstractmethod
    def list_mail_providers(self) -> List[MailProvider]:
        pass

