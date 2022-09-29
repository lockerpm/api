import re

from django.db import models, transaction

from cystack_models.models.users.users import User
from cystack_models.models.relay.relay_domains import RelayDomain
from shared.constants.relay_address import DEFAULT_RELAY_DOMAIN
from shared.constants.relay_blacklist import RELAY_BAD_WORDS, RELAY_BLOCKLISTED, RELAY_LOCKER_BLOCKED_CHARACTER
from shared.utils.app import now


class MaxRelaySubdomainReachedException(BaseException):
    """
    The max relay subdomain is reached
    """



class RelaySubdomain(models.Model):
    subdomain = models.CharField(max_length=128, db_index=True)
    created_time = models.FloatField()
    is_deleted = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="relay_subdomains")
    domain = models.ForeignKey(RelayDomain, on_delete=models.CASCADE, related_name="relay_subdomains")

    class Meta:
        db_table = 'cs_relay_subdomains'
        unique_together = ('subdomain', 'domain')

    @classmethod
    def create_atomic(cls, user_id, subdomain: str, domain_id: str = DEFAULT_RELAY_DOMAIN, is_deleted=False):
        with transaction.atomic():
            try:
                user = User.objects.filter(user_id=user_id).select_for_update().get()
            except User.DoesNotExist:
                raise
            if user.relay_subdomains.filter(is_deleted=False).exists():
                raise MaxRelaySubdomainReachedException
            return cls.create(user, subdomain=subdomain, domain_id=domain_id, is_deleted=is_deleted)

    @classmethod
    def create(cls, user, subdomain: str, domain_id: str = DEFAULT_RELAY_DOMAIN, is_deleted=False):
        new_relay_subdomain = cls(
            user=user, subdomain=subdomain, domain_id=domain_id, created_time=now(), is_deleted=is_deleted
        )
        new_relay_subdomain.save()
        return new_relay_subdomain

    @classmethod
    def valid_subdomain(cls, subdomain) -> bool:
        address_pattern_valid = cls.valid_address_pattern(subdomain)
        address_contains_bad_word = cls.has_bad_words(subdomain)
        address_is_blocklisted = cls.is_blocklisted(subdomain)
        address_is_locker_blocked = cls.is_locker_blocked(subdomain)

        if address_contains_bad_word or address_is_blocklisted or not address_pattern_valid or \
                address_is_locker_blocked:
            return False
        return True

    @classmethod
    def valid_address_pattern(cls, address):
        # The address can't start or end with a hyphen, must be 1 - 63 lowercase alphanumeric characters
        valid_address_pattern = re.compile("^(?!-)[a-z0-9-]{1,63}(?<!-)$")
        return valid_address_pattern.match(address) is not None

    @classmethod
    def has_bad_words(cls, value):
        for bad_word in RELAY_BAD_WORDS:
            bad_word = bad_word.strip()
            if len(bad_word) <= 4 and bad_word == value:
                return True
            if len(bad_word) > 4 and bad_word in value:
                return True
        return False

    @classmethod
    def is_blocklisted(cls, value):
        return any(blocked_word == value for blocked_word in RELAY_BLOCKLISTED)

    @classmethod
    def is_locker_blocked(cls, value):
        for blocked_word in RELAY_LOCKER_BLOCKED_CHARACTER:
            if blocked_word in value:
                return True
        return False

    def soft_delete(self):
        self.is_deleted = True
        self.save()
