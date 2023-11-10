import uuid

from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.utils.app import now


class AbstractExcludeDomainORM(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    created_time = models.FloatField()
    domain = models.CharField(max_length=255)
    user = models.ForeignKey(
        locker_server_settings.LS_USER_MODEL, on_delete=models.CASCADE, related_name="exclude_domains"
    )

    class Meta:
        abstract = True
        unique_together = ('user', 'domain')

    @classmethod
    def retrieve_or_create(cls, domain, user_id):
        exclude_domain, is_created = cls.objects.get_or_create(
            domain=domain, user_id=user_id, defaults={
                "user_id": user_id, "domain": domain, "created_time": now()
            }
        )
        return exclude_domain
