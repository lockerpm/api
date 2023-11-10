import json

from django.db import models, transaction, IntegrityError

from locker_server.api_orm.models.configurations.mail_providers import MailProviderORM


class MailConfigurationORM(models.Model):
    mail_provider = models.ForeignKey(MailProviderORM, on_delete=models.CASCADE, related_name="mail_configurations")
    mail_provider_options = models.CharField(max_length=512, null=True, blank=True, default="")
    sending_domain = models.CharField(max_length=255, blank=True, null=True, default=None)
    from_email = models.EmailField(max_length=255, blank=True, null=True, default=None)
    from_name = models.CharField(max_length=255, blank=True, null=True, default=None)

    class Meta:
        db_table = 'cs_mail_configurations'

    @classmethod
    def create(cls, **data):
        with transaction.atomic():
            try:
                mail_config_orm = cls.objects.get()
            except cls.DoesNotExist:
                mail_config_orm = cls.objects.create(
                    mail_provider_id=data.get("mail_provider_id"),
                    mail_provider_options=data.get("mail_provider_options"),
                    sending_domain=data.get("sending_domain"),
                    from_email=data.get("from_email"),
                    from_name=data.get("from_name")
                )
            return mail_config_orm

    def get_mail_provider_option(self):
        if not self.mail_provider_options:
            return {}
        try:
            return json.loads(str(self.mail_provider_options))
        except json.JSONDecodeError:
            return self.mail_provider_options
