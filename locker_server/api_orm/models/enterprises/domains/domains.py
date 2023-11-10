from django.conf import settings

from locker_server.api_orm.abstracts.enterprises.domains.domains import AbstractDomainORM
from locker_server.shared.constants.domain_ownership import TYPE_DNS_TXT
from locker_server.shared.utils.app import now


class DomainORM(AbstractDomainORM):
    class Meta(AbstractDomainORM.Meta):
        swappable = 'LS_ENTERPRISE_DOMAIN_MODEL'
        db_table = 'e_domains'

    @classmethod
    def create(cls, **data):
        enterprise_id = data.get("enterprise_id")
        domain = data.get("domain")
        root_domain = data.get("root_domain")
        verification = data.get("verification", False)
        created_time = now()
        updated_time = now()
        new_domain = cls(
            enterprise_id=enterprise_id,
            domain=domain,
            root_domain=root_domain,
            verification=verification,
            created_time=created_time,
            updated_time=updated_time
        )

        new_domain.save()

        # Create domain ownerships
        new_domain.domain_ownership.model.create(domain=new_domain)

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
