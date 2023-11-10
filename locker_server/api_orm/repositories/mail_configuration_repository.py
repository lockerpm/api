from typing import Optional

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models import MailConfigurationORM
from locker_server.core.entities.configuration.mail_configuration import MailConfiguration
from locker_server.core.repositories.mail_configuration_repository import MailConfigurationRepository
from locker_server.shared.constants.mail_provider import MAIL_PROVIDER_SMTP

ModelParser = get_model_parser()


class MailConfigurationORMRepository(MailConfigurationRepository):
    # ------------------------ List MailConfiguration resource ------------------- #

    # ------------------------ Get MailConfiguration resource --------------------- #
    def get_mail_configuration(self) -> Optional[MailConfiguration]:
        try:
            mail_configuration_orm = MailConfigurationORM.objects.get()
            return ModelParser.configuration_parser().parse_mail_configuration(
                mail_configuration_orm=mail_configuration_orm
            )
        except MailConfigurationORM.DoesNotExist:
            return None

    # ------------------------ Create MailConfiguration resource --------------------- #

    # ------------------------ Update MailConfiguration resource --------------------- #
    def update_mail_configuration(self, mail_config_data) -> MailConfiguration:
        mail_provider_id = mail_config_data.get("mail_provider_id") or mail_config_data.get("mail_provider")
        try:
            mail_configuration_orm = MailConfigurationORM.objects.get()
        except MailConfigurationORM.DoesNotExist:
            mail_configuration_orm = MailConfigurationORM.create(**{
                "mail_provider_id": mail_provider_id or MAIL_PROVIDER_SMTP
            })
        mail_configuration_orm.mail_provider_id = mail_provider_id or mail_configuration_orm.mail_provider_id
        mail_configuration_orm.mail_provider_options = mail_config_data.get(
            "mail_provider_options", mail_configuration_orm.mail_provider_options
        )
        mail_configuration_orm.sending_domain = mail_config_data.get(
            "sending_domain", mail_configuration_orm.sending_domain
        )
        mail_configuration_orm.from_email = mail_config_data.get(
            "from_email", mail_configuration_orm.from_email
        )
        mail_configuration_orm.from_name = mail_config_data.get(
            "from_name", mail_configuration_orm.from_name
        )
        mail_configuration_orm.save()
        return ModelParser.configuration_parser().parse_mail_configuration(
            mail_configuration_orm=mail_configuration_orm
        )

    # ------------------------ Delete MailConfiguration resource --------------------- #
    def destroy_mail_configuration(self):
        MailConfigurationORM.objects.filter().delete()
