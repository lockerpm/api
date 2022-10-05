from django.conf import settings
from django.db import models

from cystack_models.models.enterprises.enterprises import Enterprise
from shared.constants.domain_ownership import TYPE_DNS_TXT
from shared.utils.app import now


class Domain(models.Model):
    id = models.AutoField(primary_key=True)
    created_time = models.FloatField()
    updated_time = models.FloatField(null=True)
    domain = models.CharField(max_length=128)
    root_domain = models.CharField(max_length=128)
    verification = models.BooleanField(default=False)
    auto_approve = models.BooleanField(default=False)
    is_notify_failed = models.BooleanField(default=False)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name="domains")

    class Meta:
        db_table = 'e_domains'

    @classmethod
    def create(cls, enterprise: Enterprise, domain: str, root_domain: str, verification: bool = False):
        new_domain = cls(
            enterprise=enterprise, domain=domain, root_domain=root_domain, verification=verification,
            created_time=now(), updated_time=now()
        )
        new_domain.save()

        # Create domain ownerships
        new_domain.domain_ownership.model.create(new_domain)

        return new_domain

    def set_verified(self):
        self.verification = True
        self.updated_time = now()
        self.save()

    def get_verifications(self):
        results = []
        ownerships = self.domain_ownership.select_related('ownership')
        for ownership in ownerships:
            results.append({
                "ownership_id": ownership.ownership_id,
                "ownership_description": ownership.ownership.description,
                "key": ownership.key,
                "value": ownership.value
            })
        return results

    def check_verification(self) -> bool:
        domain_ownerships = self.domain_ownership.all().select_related('ownership')
        for domain_ownership in domain_ownerships:
            if domain_ownership.ownership_id == TYPE_DNS_TXT:
                if domain_ownership.verify_dns("TXT") or domain_ownership.verify_dns("CNAME") or \
                        self.domain in settings.TEST_DOMAINS:
                    domain_ownership.set_verified()
                    self.set_verified()
                    return True
        return False
