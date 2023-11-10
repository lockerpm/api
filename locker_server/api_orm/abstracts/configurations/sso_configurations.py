import json
import uuid

from django.db import models

from locker_server.api_orm.models.configurations.sso_providers import SSOProviderORM
from locker_server.settings import locker_server_settings


class AbstractSSOConfigurationORM(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    identifier = models.CharField(max_length=255, unique=True, db_index=True)
    sso_provider_options = models.CharField(max_length=1024, null=True, blank=True, default="")
    enabled = models.BooleanField(null=True, default=False)
    creation_date = models.FloatField()
    revision_date = models.FloatField(null=True)

    sso_provider = models.ForeignKey(SSOProviderORM, on_delete=models.CASCADE, related_name="sso_configurations")
    created_by = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.SET_NULL, related_name="created_sso_configurations",
        null=True
    )

    class Meta:
        abstract = True

    @classmethod
    def create(cls, **data):
        raise NotImplementedError

    def get_sso_provider_option(self):
        if not self.sso_provider_options:
            return {}
        try:
            return json.loads(str(self.sso_provider_options))
        except json.JSONDecodeError:
            return self.sso_provider_options
