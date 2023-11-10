from typing import List

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.configurations.mail_providers import MailProviderORM
from locker_server.core.entities.configuration.mail_provider import MailProvider
from locker_server.core.repositories.mail_provider_repository import MailProviderRepository

ModelParser = get_model_parser()


class MailProviderORMRepository(MailProviderRepository):
    def list_mail_providers(self) -> List[MailProvider]:
        mail_providers_orm = MailProviderORM.objects.all().order_by('order_index')
        return [
            ModelParser.configuration_parser().parse_mail_provider(mail_provider_orm=mail_provider_orm)
            for mail_provider_orm in mail_providers_orm
        ]
