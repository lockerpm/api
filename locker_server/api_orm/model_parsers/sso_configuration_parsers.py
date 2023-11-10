from locker_server.api_orm.model_parsers.wrapper_specific_model_parser import get_specific_model_parser
from locker_server.api_orm.models import SSOProviderORM, SSOConfigurationORM
from locker_server.core.entities.sso_configuration.sso_configuration import SSOConfiguration
from locker_server.core.entities.sso_configuration.sso_provider import SSOProvider


class SSOConfigurationParser:
    @classmethod
    def parse_sso_provider(cls, sso_provider_orm: SSOProviderORM) -> SSOProvider:
        return SSOProvider(
            sso_provider_id=sso_provider_orm.id,
            name=sso_provider_orm.name
        )

    @classmethod
    def parse_sso_configuration(cls, sso_configuration_orm: SSOConfigurationORM) -> SSOConfiguration:
        user_parser = get_specific_model_parser("UserParser")
        return SSOConfiguration(
            sso_configuration_id=sso_configuration_orm.id,
            sso_provider=cls.parse_sso_provider(sso_provider_orm=sso_configuration_orm.sso_provider),
            sso_provider_options=sso_configuration_orm.get_sso_provider_option(),
            enabled=sso_configuration_orm.enabled,
            identifier=sso_configuration_orm.identifier,
            creation_date=sso_configuration_orm.creation_date,
            revision_date=sso_configuration_orm.revision_date,
            created_by=user_parser.parse_user(
                user_orm=sso_configuration_orm.created_by
            ) if sso_configuration_orm.created_by else None,
        )
