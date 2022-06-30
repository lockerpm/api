import hashlib
import dns.resolver

from django.db import models

from cystack_models.models.domains.domains import Domain
from cystack_models.models.domains.ownership import Ownership
from shared.constants.domain_ownership import TYPE_DNS_TXT
from shared.utils.app import random_n_digit


class DomainOwnership(models.Model):
    key = models.CharField(max_length=128)
    value = models.CharField(max_length=128)
    verification = models.BooleanField(default=False)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="domain_ownership")
    ownership = models.ForeignKey(Ownership, on_delete=models.CASCADE, related_name="domain_ownership")

    class Meta:
        db_table = 'cs_domain_ownership'
        unique_together = ('domain', 'ownership')

    @classmethod
    def gen_verification_code(cls):
        verification_code = hashlib.md5(random_n_digit(15).encode('utf-8')).hexdigest()
        return verification_code

    @classmethod
    def create(cls, domain: Domain):
        ownerships = Ownership.objects.all()
        verification_code = cls.gen_verification_code()
        for ownership in ownerships:
            if ownership.id == TYPE_DNS_TXT:
                key = "@"
                value = "locker-verification={}".format(verification_code)
                # key = 'locker-verification.{}'.format(domain.domain)
                cls.objects.create(key=key, value=value, domain=domain, ownership=ownership)

    def set_verified(self):
        self.verification = True
        self.save()

    def verify_dns(self, dns_type):
        """
        :param dns_type: CNAME / TXT
        :return:
        """
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['1.1.1.1', '8.8.8.8', '8.8.4.4']
        try:
            answers = resolver.query(self.key, dns_type)
            for data in answers:
                if str(data).strip('"')[:-1] == self.value or str(data).strip('"') == self.value:
                    return True
        except Exception as e:
            return False
        return False
