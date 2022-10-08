import re
from hashlib import sha256

from django.db import models, transaction

from cystack_models.models.relay.relay_domains import RelayDomain
from cystack_models.models.relay.relay_subdomains import RelaySubdomain
from cystack_models.models.relay.deleted_relay_addresses import DeletedRelayAddress
from cystack_models.models.users.users import User
from shared.constants.relay_address import DEFAULT_RELAY_DOMAIN, MAX_FREE_RElAY_DOMAIN
from shared.constants.relay_blacklist import RELAY_BAD_WORDS, RELAY_BLOCKLISTED, RELAY_LOCKER_BLOCKED_CHARACTER
from shared.utils.app import random_n_digit, now


class MaxRelayAddressReachedException(BaseException):
    """
    The max relay address is reached
    """


class RelayAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="relay_addresses")
    address = models.CharField(max_length=64, unique=True)
    subdomain = models.ForeignKey(
        RelaySubdomain, on_delete=models.CASCADE, related_name="relay_addresses", null=True, default=None
    )
    domain = models.ForeignKey(RelayDomain, on_delete=models.CASCADE, related_name="relay_addresses")
    enabled = models.BooleanField(default=True)
    block_spam = models.BooleanField(default=False)
    description = models.CharField(max_length=64, blank=True)
    created_time = models.FloatField()
    updated_time = models.FloatField(null=True)
    num_forwarded = models.PositiveIntegerField(default=0)
    num_blocked = models.PositiveIntegerField(default=0)
    num_replied = models.PositiveIntegerField(default=0)
    num_spam = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'cs_relay_addresses'

    @property
    def full_address(self):
        if self.subdomain:
            return f"{self.address}@{self.subdomain.subdomain}.{self.domain_id}"
        return f"{self.address}@{self.domain_id}"

    @property
    def subdomain_string(self):
        if self.subdomain:
            return self.subdomain.subdomain
        return None

    @classmethod
    def create_atomic(cls, user_id, **data):
        with transaction.atomic():
            try:
                user = User.objects.filter(user_id=user_id).select_for_update().get()
            except User.DoesNotExist:
                raise
            if data.get("allow_relay_premium", False) is False and \
                    user.relay_addresses.all().count() >= MAX_FREE_RElAY_DOMAIN:
                raise MaxRelayAddressReachedException
            return cls.create(user, **data)

    @classmethod
    def create(cls, user: User, **data):
        domain_id = data.get("domain_id") or DEFAULT_RELAY_DOMAIN
        description = data.get("description", "")
        subdomain_obj = data.get("subdomain")
        while True:
            address = random_n_digit(n=6)
            if cls.objects.filter(address=address).exists() is True:
                continue
            if cls.valid_address(address=address, domain=domain_id) is False:
                continue
            break
        new_relay_address = cls(
            user=user, address=address, domain_id=domain_id, subdomain=subdomain_obj,
            created_time=now(), description=description,
        )
        new_relay_address.save()

        return new_relay_address

    @classmethod
    def valid_address(cls, address, domain) -> bool:
        address_pattern_valid = cls.valid_address_pattern(address)
        address_contains_bad_word = cls.has_bad_words(address)
        address_is_blocklisted = cls.is_blocklisted(address)
        address_is_locker_blocked = cls.is_locker_blocked(address)
        address_already_deleted = DeletedRelayAddress.objects.filter(
            address_hash=cls.hash_address(address, domain)
        ).exists()
        if address_already_deleted is True or address_contains_bad_word or address_is_blocklisted or \
                not address_pattern_valid or address_is_locker_blocked:
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

    @classmethod
    def hash_address(cls, address, domain):
        return sha256(f"{address}@{domain}".encode("utf-8")).hexdigest()

    def delete_permanently(self):
        if self.subdomain:
            full_domain = f"{self.subdomain.subdomain}.{self.domain_id}"
        else:
            full_domain = self.domain_id
        deleted_address = DeletedRelayAddress.objects.create(
            address_hash=RelayAddress.hash_address(self.address, full_domain),
            num_forwarded=self.num_forwarded,
            num_blocked=self.num_blocked,
            num_replied=self.num_replied,
            num_spam=self.num_spam,
        )
        deleted_address.save()
        # Remove relay address
        self.delete()
