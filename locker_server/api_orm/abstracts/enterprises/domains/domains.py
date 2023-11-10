from django.db import models

from locker_server.settings import locker_server_settings


class AbstractDomainORM(models.Model):
    id = models.AutoField(primary_key=True)
    created_time = models.FloatField()
    updated_time = models.FloatField(null=True)
    domain = models.CharField(max_length=128)
    root_domain = models.CharField(max_length=128)
    verification = models.BooleanField(default=False)
    auto_approve = models.BooleanField(default=False)
    is_notify_failed = models.BooleanField(default=False)
    enterprise = models.ForeignKey(
        locker_server_settings.LS_ENTERPRISE_MODEL, on_delete=models.CASCADE, related_name="domains"
    )

    class Meta:
        abstract = True

    @classmethod
    def create(cls, enterprise, domain: str, root_domain: str, verification: bool = False):
        raise NotImplementedError
