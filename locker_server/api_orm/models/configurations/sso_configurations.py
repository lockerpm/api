from django.db import transaction

from locker_server.api_orm.abstracts.configurations.sso_configurations import AbstractSSOConfigurationORM
from locker_server.shared.utils.app import now


class SSOConfigurationORM(AbstractSSOConfigurationORM):
    class Meta(AbstractSSOConfigurationORM.Meta):
        swappable = 'LS_SSO_CONFIGURATION_MODEL'
        db_table = 'cs_sso_configurations'

    @classmethod
    def create(cls, **data):
        with transaction.atomic():
            try:
                sso_config_orm = cls.objects.get()
            except cls.DoesNotExist:
                sso_config_orm = cls(
                    created_by_id=data.get("created_by_id"),
                    sso_provider_id=data.get("sso_provider_id"),
                    identifier=data.get("identifier"),
                    enabled=data.get("enabled", False),
                    sso_provider_options=data.get("sso_provider_options"),
                    creation_date=data.get("creation_date", now())
                )
                sso_config_orm.save()
            return sso_config_orm
