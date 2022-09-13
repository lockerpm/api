from django.db import models

from cystack_models.models.enterprises.enterprises import Enterprise
from shared.utils.app import now


class EnterpriseBillingContact(models.Model):
    created_time = models.FloatField()
    email = models.EmailField(max_length=128)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="billing_contacts")

    class Meta:
        db_table = 'e_billing_contacts'
        unique_together = ('enterprise', 'email')

    @classmethod
    def retrieve_or_create(cls, enterprise: Enterprise, email: str):
        contact, is_created = cls.objects.get_or_create(
            enterprise=enterprise, email=email,
            defaults={"enterprise": enterprise, "email": email, "created_time": now()}
        )
        return contact
