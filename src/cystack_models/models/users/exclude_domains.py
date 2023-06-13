import uuid

from django.db import models

from cystack_models.models.users.users import User
from shared.utils.app import now


class ExcludeDomain(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid4)
    created_time = models.FloatField()
    domain = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="exclude_domains")

    class Meta:
        db_table = 'cs_exclude_domains'
        unique_together = ('user', 'domain')

    @classmethod
    def retrieve_or_create(cls, domain, user):
        exclude_domain, is_created = cls.objects.get_or_create(
            domain=domain, user=user, defaults={
                "user": user, "domain": domain, "created_time": now()
            }
        )
        return exclude_domain

