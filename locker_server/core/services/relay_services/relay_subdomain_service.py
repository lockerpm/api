import json
import os
import re
from typing import Optional

from locker_server.core.entities.relay.relay_address import RelayAddress
from locker_server.core.repositories.relay_repositories.deleted_relay_address_repository import \
    DeletedRelayAddressRepository
from locker_server.core.repositories.relay_repositories.relay_address_repository import RelayAddressRepository
from locker_server.core.repositories.relay_repositories.relay_subdomain_repository import RelaySubdomainRepository

from locker_server.core.exceptions.relay_exceptions.relay_subdomain_exception import *
from locker_server.core.exceptions.user_exception import UserDoesNotExistException
from locker_server.core.repositories.user_repository import UserRepository
from locker_server.core.entities.relay.relay_subdomain import RelaySubdomain
from locker_server.shared.constants.relay_blacklist import RELAY_BAD_WORDS, RELAY_BLOCKLISTED, \
    RELAY_LOCKER_BLOCKED_CHARACTER
from locker_server.shared.external_services.sqs.sqs import sqs_service


class RelaySubdomainService:
    """
    This class represents Use Cases related relay subdomain
    """

    def __init__(self, relay_subdomain_repository: RelaySubdomainRepository,
                 user_repository: UserRepository,
                 relay_address_repository: RelayAddressRepository,
                 deleted_relay_address_repository: DeletedRelayAddressRepository
                 ):
        self.user_repository = user_repository
        self.relay_subdomain_repository = relay_subdomain_repository
        self.relay_address_repository = relay_address_repository
        self.deleted_relay_address_repository = deleted_relay_address_repository

    @staticmethod
    def valid_subdomain_pattern(address):
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

    def list_user_relay_subdomains(self, user_id: int, **filters):
        return self.relay_subdomain_repository.list_user_relay_subdomains(
            user_id=user_id,
            **filters
        )

    def create_relay_subdomain(self, user_id: int, relay_subdomain_create_data) -> RelaySubdomain:
        subdomain = relay_subdomain_create_data.get("subdomain")
        is_valid_subdomain = self.check_valid_address(subdomain=subdomain)
        if not is_valid_subdomain:
            raise RelaySubdomainInvalidException
        existed_relay_subdomain = self.relay_subdomain_repository.get_relay_subdomain_by_subdomain(subdomain=subdomain)
        if existed_relay_subdomain:
            raise RelaySubdomainExistedException
        relay_subdomain_create_data.update({
            "user_id": user_id
        })
        new_relay_subdomain = self.relay_subdomain_repository.create_atomic_relay_subdomain(
            relay_subdomain_create_data=relay_subdomain_create_data
        )
        if not new_relay_subdomain:
            raise MaxRelaySubdomainReachedException

        if os.getenv("PROD_ENV") == "prod":
            action_msg = {
                'action': 'create',
                'domain': f"{new_relay_subdomain.subdomain}.{new_relay_subdomain.domain.relay_domain_id}"
            }
            create_msg = {'Type': 'DomainIdentity', 'Message': json.dumps(action_msg)}
            sqs_service.send_message(message_body=json.dumps(create_msg))

        return new_relay_subdomain

    def update_relay_subdomain(self, user_id: str, relay_subdomain: RelaySubdomain,
                               relay_subdomain_update_data) -> Optional[RelaySubdomain]:
        old_subdomain = relay_subdomain.subdomain
        new_subdomain = relay_subdomain_update_data.get("subdomain")
        if old_subdomain == new_subdomain:
            return relay_subdomain
        relay_subdomain_id = relay_subdomain.relay_subdomain_id
        if not self.check_valid_address(subdomain=new_subdomain):
            raise RelaySubdomainInvalidException
        is_used_subdomain = self.relay_subdomain_repository.check_used_subdomain(
            user_id=user_id,
            subdomain=new_subdomain
        )
        if is_used_subdomain:
            raise RelaySubdomainAlreadyUsedException
        updated_relay_subdomain = self.relay_subdomain_repository.update_relay_subdomain(
            relay_subdomain_id=relay_subdomain_id,
            relay_subdomain_update_data=relay_subdomain_update_data
        )
        if not updated_relay_subdomain:
            raise RelaySubdomainDoesNotExistException

        # Delete all old relay addresses of this subdomain
        self.delete_old_addresses_of_subdomain(relay_subdomain=updated_relay_subdomain)
        # Create deletion SQS job
        if os.getenv("PROD_ENV") == "prod":
            action_delete_msg = {
                'action': 'delete',
                'domain': f"{old_subdomain}.{updated_relay_subdomain.domain.relay_domain_id}"
            }
            delete_msg = {'Type': 'DomainIdentity', 'Message': json.dumps(action_delete_msg)}
            sqs_service.send_message(message_body=json.dumps(delete_msg))

        # Save subdomain object as deleted
        self.relay_subdomain_repository.create_relay_subdomain(
            relay_subdomain_create_data={"user_id": user_id, "subdomain": old_subdomain, "is_deleted": True}
        )

        # Send creation job to SQS
        if os.getenv("PROD_ENV") == "prod":
            action_create_msg = {
                'action': 'create',
                'domain': f"{new_subdomain}.{updated_relay_subdomain.domain.relay_domain_id}"
            }
            create_msg = {'Type': 'DomainIdentity', 'Message': json.dumps(action_create_msg)}
            sqs_service.send_message(message_body=json.dumps(create_msg))

        return updated_relay_subdomain

    def get_first_subdomain_by_domain_id(self, user_id: str, domain_id: str) -> RelaySubdomain:
        return self.relay_subdomain_repository.get_first_subdomain_by_domain_id(
            user_id=user_id,
            domain_id=domain_id
        )

    def get_relay_subdomain_by_id(self, relay_subdomain_id) -> Optional[RelaySubdomain]:
        relay_subdomain = self.relay_subdomain_repository.get_relay_subdomain_by_id(
            relay_subdomain_id=relay_subdomain_id
        )
        if not relay_subdomain:
            raise RelaySubdomainDoesNotExistException
        return relay_subdomain

    def soft_delete_relay_subdomain(self, relay_subdomain: RelaySubdomain) -> RelaySubdomain:
        relay_subdomain_update_data = {
            "is_deleted": True
        }
        soft_deleted_subdomain = self.relay_subdomain_repository.update_relay_subdomain(
            relay_subdomain_id=relay_subdomain.relay_subdomain_id,
            relay_subdomain_update_data=relay_subdomain_update_data
        )
        if not soft_deleted_subdomain:
            raise RelaySubdomainDoesNotExistException

        self.delete_old_addresses_of_subdomain(relay_subdomain=relay_subdomain)

        # Create deletion SQS job
        if os.getenv("PROD_ENV") == "prod":
            action_delete_msg = {
                'action': 'delete',
                'domain': f"{relay_subdomain.subdomain}.{relay_subdomain.domain.relay_domain_id}"
            }
            delete_msg = {'Type': 'DomainIdentity', 'Message': json.dumps(action_delete_msg)}
            sqs_service.send_message(message_body=json.dumps(delete_msg))
        return soft_deleted_subdomain

    def delete_old_addresses_of_subdomain(self, relay_subdomain: RelaySubdomain):
        # Delete all old relay addresses of this subdomain
        relay_addresses = self.relay_address_repository.list_relay_addresses(**{
            "subdomain_id": relay_subdomain.relay_subdomain_id
        })
        for relay_address in relay_addresses:
            if relay_address.subdomain:
                full_domain = f"{relay_address.subdomain.subdomain}.{relay_address.domain.relay_domain_id}"
            else:
                full_domain = relay_address.domain.relay_domain_id
            deleted_relay_address = self.relay_address_repository.delete_relay_address_by_id(
                relay_address_id=relay_address.relay_address_id
            )
            if deleted_relay_address:
                self.deleted_relay_address_repository.create_deleted_relay_address(
                    deleted_relay_address_create_data={
                        "address_hash": RelayAddress.hash_address(address=relay_address.address,
                                                                  domain=full_domain),
                        "num_forwarded": relay_address.num_forwarded,
                        "num_blocked": relay_address.num_blocked,
                        "num_replied": relay_address.num_replied,
                        "num_spam": relay_address.num_spam,
                    }
                )

    def check_valid_address(self, subdomain: str) -> bool:
        address_pattern_valid = self.valid_subdomain_pattern(subdomain)
        address_contains_bad_word = self.has_bad_words(subdomain)
        address_is_blocklisted = self.is_blocklisted(subdomain)
        address_is_locker_blocked = self.is_locker_blocked(subdomain)

        if address_contains_bad_word or address_is_blocklisted or not address_pattern_valid or \
                address_is_locker_blocked:
            return False
        return True

