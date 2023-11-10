import re
from hashlib import sha256
from typing import Optional, NoReturn
from locker_server.core.repositories.relay_repositories.relay_address_repository import RelayAddressRepository
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.core.repositories.relay_repositories.deleted_relay_address_repository import \
    DeletedRelayAddressRepository

from locker_server.core.exceptions.relay_exceptions.relay_address_exception import *
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.core.entities.relay.relay_address import RelayAddress
from locker_server.shared.constants.relay_address import MAX_FREE_RElAY_DOMAIN, DEFAULT_RELAY_DOMAIN
from locker_server.shared.constants.relay_blacklist import RELAY_BAD_WORDS, RELAY_BLOCKLISTED, \
    RELAY_LOCKER_BLOCKED_CHARACTER
from locker_server.shared.utils.app import random_n_digit


class RelayAddressService:
    """
    This class represents Use Cases related relay address
    """

    def __init__(self, relay_address_repository: RelayAddressRepository, user_repository: UserRepository,
                 deleted_relay_address_repository: DeletedRelayAddressRepository):
        self.relay_address_repository = relay_address_repository
        self.user_repository = user_repository
        self.deleted_relay_address_repository = deleted_relay_address_repository

    @staticmethod
    def valid_address_pattern(address):
        # The address can't start or end with a hyphen, must be 1 - 63 lowercase alphanumeric characters
        valid_address_pattern = re.compile("^(?!-)[a-z0-9-]{1,63}(?<!-)$")
        return valid_address_pattern.match(address) is not None

    @staticmethod
    def has_bad_words(value):
        for bad_word in RELAY_BAD_WORDS:
            bad_word = bad_word.strip()
            if len(bad_word) <= 4 and bad_word == value:
                return True
            if len(bad_word) > 4 and bad_word in value:
                return True
        return False

    @staticmethod
    def is_blocklisted(value):
        return any(blocked_word == value for blocked_word in RELAY_BLOCKLISTED)

    @staticmethod
    def is_locker_blocked(value):
        for blocked_word in RELAY_LOCKER_BLOCKED_CHARACTER:
            if blocked_word in value:
                return True
        return False

    def generate_relay_address(self, domain_id: str) -> str:
        while True:
            address = random_n_digit(n=6)
            if self.relay_address_repository.get_relay_address_by_address(address=address):
                continue
            if self.check_valid_address(address=address, domain=domain_id) is False:
                continue
            return address

    def list_user_relay_addresses(self, user_id: int, **filters):
        return self.relay_address_repository.list_user_relay_addresses(
            user_id=user_id,
            **filters
        )

    def get_relay_address_by_id(self, relay_address_id) -> Optional[RelayAddress]:
        relay_address = self.relay_address_repository.get_relay_address_by_id(relay_address_id=relay_address_id)
        if not relay_address:
            raise RelayAddressDoesNotExistException
        return relay_address

    def create_relay_address(self, user_id: int, relay_address_create_data) -> Optional[RelayAddress]:
        user = self.user_repository.get_user_by_id(user_id=user_id)
        if not user:
            raise UserDoesNotExistException
        address = self.generate_relay_address(
            domain_id=relay_address_create_data.get("domain_id") or DEFAULT_RELAY_DOMAIN
        )
        relay_address_create_data.update({
            'user_id': user_id,
            'address': address
        })
        new_relay_address = self.relay_address_repository.create_relay_address(relay_address_create_data)
        if not new_relay_address:
            raise RelayAddressReachedException
        return new_relay_address

    def update_relay_address(self, user_id: int, relay_address: RelayAddress,
                             relay_address_update_data: dict, allow_relay_premium=False) -> Optional[RelayAddress]:
        address = relay_address_update_data.get("address") or relay_address.address

        if address != relay_address.address:
            # Only allow update the first address
            oldest_relay_address = self.relay_address_repository.get_oldest_user_relay_address(user_id=user_id)
            if not oldest_relay_address or oldest_relay_address.relay_address_id != relay_address.relay_address_id:
                raise RelayAddressUpdateDeniedException
            existed_address = self.relay_address_repository.get_relay_address_by_address(address=address)
            if existed_address:
                raise RelayAddressExistedException
            valid_address = self.check_valid_address(address=address, domain=relay_address.domain.relay_domain_id)
            if not valid_address:
                raise RelayAddressInvalidException

        relay_address_update_data.update({'address': address})
        if not allow_relay_premium:
            relay_address_update_data.update({
                'enabled': relay_address.enabled,
                'block_spam': relay_address.block_spam
            })
        relay_address = self.relay_address_repository.update_relay_address(
            relay_address_id=relay_address.relay_address_id,
            relay_address_update_data=relay_address_update_data
        )
        if not relay_address:
            raise RelayAddressDoesNotExistException
        return relay_address

    def delete_relay_address(self, relay_address: RelayAddress) -> bool:
        if relay_address.subdomain:
            full_domain = f"{relay_address.subdomain.subdomain}.{relay_address.domain.relay_domain_id}"
        else:
            full_domain = relay_address.domain.relay_domain_id
        deleted_relay_address = self.relay_address_repository.delete_relay_address_by_id(
            relay_address_id=relay_address.relay_address_id
        )
        if not deleted_relay_address:
            raise RelayAddressDoesNotExistException
        self.deleted_relay_address_repository.create_deleted_relay_address(
            deleted_relay_address_create_data={
                "address_hash": RelayAddress.hash_address(address=relay_address.address, domain=full_domain),
                "num_forwarded": relay_address.num_forwarded,
                "num_blocked": relay_address.num_blocked,
                "num_replied": relay_address.num_replied,
                "num_spam": relay_address.num_spam,
            }
        )
        return relay_address.relay_address_id

    def delete_relay_addresses_by_subdomain_id(self, subdomain_id: str):
        relay_addresses = self.relay_address_repository.list_relay_addresses(**{
            "subdomain_id": subdomain_id
        })
        for relay_address in relay_addresses:
            try:
                self.delete_relay_address(relay_address=relay_address)
            except RelayAddressDoesNotExistException:
                continue

    def update_block_spam(self, relay_address: RelayAddress) -> Optional[RelayAddress]:
        relay_address_update_data = {
            'block_spam': not relay_address.block_spam
        }
        updated_relay_address = self.relay_address_repository.update_relay_address(
            relay_address_id=relay_address.relay_address_id,
            relay_address_update_data=relay_address_update_data
        )
        if not updated_relay_address:
            raise RelayAddressDoesNotExistException
        return updated_relay_address

    def update_enabled(self, relay_address: RelayAddress) -> Optional[RelayAddress]:
        relay_address_update_data = {
            'enabled': not relay_address.enabled
        }
        updated_relay_address = self.relay_address_repository.update_relay_address(
            relay_address_id=relay_address.relay_address_id,
            relay_address_update_data=relay_address_update_data
        )
        if not updated_relay_address:
            raise RelayAddressDoesNotExistException
        return updated_relay_address

    def get_relay_address_by_full_domain(self, address: str, domain_id: str,
                                         subdomain: str = None) -> Optional[RelayAddress]:
        relay_address = self.relay_address_repository.get_relay_address_by_full_domain(
            address=address,
            domain_id=domain_id,
            subdomain=subdomain
        )
        return relay_address

    def check_valid_address(self, address: str, domain: str) -> bool:
        address_pattern_valid = self.valid_address_pattern(address)
        address_contains_bad_word = self.has_bad_words(address)
        address_is_blocklisted = self.is_blocklisted(address)
        address_is_locker_blocked = self.is_locker_blocked(address)
        address_already_deleted = self.deleted_relay_address_repository.check_exist_address_hash(
            address_hash=RelayAddress.hash_address(address, domain)
        )
        if address_already_deleted is True or address_contains_bad_word or address_is_blocklisted or \
                not address_pattern_valid or address_is_locker_blocked:
            return False
        return True

    def update_relay_address_statistic(self, relay_address_id: str, statistic_type: str, amount: int) -> [Optional]:
        relay_address = self.relay_address_repository.update_relay_address_statistic(
            relay_address_id=relay_address_id, statistic_type=statistic_type, amount=amount
        )
        if not relay_address:
            raise RelayAddressDoesNotExistException
        return relay_address
