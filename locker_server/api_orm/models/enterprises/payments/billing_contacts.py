from django.db import models

from locker_server.settings import locker_server_settings
from locker_server.shared.utils.app import now


class EnterpriseBillingContactORM(models.Model):
    created_time = models.FloatField()
    email = models.EmailField(max_length=128)
    enterprise = models.ForeignKey(
        locker_server_settings.LS_ENTERPRISE_MODEL, on_delete=models.CASCADE, related_name="billing_contacts"
    )

    class Meta:
        db_table = 'e_billing_contacts'
        unique_together = ('enterprise', 'email')

    @classmethod
    def retrieve_or_create(cls, enterprise, email: str):
        contact, is_created = cls.objects.get_or_create(
            enterprise=enterprise, email=email,
            defaults={"enterprise": enterprise, "email": email, "created_time": now()}
        )
        return contact

    @classmethod
    def create(cls, **data):
        created_time = now()
        email = data.get("email")
        enterprise_id = data.get("enterprise_id")
        contact, is_created = cls.objects.get_or_create(
            enterprise_id=enterprise_id, email=email,
            defaults={
                "enterprise_id": enterprise_id,
                "email": email,
                "created_time": created_time
            }
        )
        return contact
