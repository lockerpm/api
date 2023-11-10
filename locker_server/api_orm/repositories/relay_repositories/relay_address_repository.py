import re
from typing import Optional, List

from django.db import transaction
from django.db.models import F

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_relay_address_model, get_relay_deleted_address_model, \
    get_user_model
from locker_server.core.entities.relay.relay_address import RelayAddress
from locker_server.core.repositories.relay_repositories.relay_address_repository import RelayAddressRepository
from locker_server.shared.constants.relay_address import DEFAULT_RELAY_DOMAIN, MAX_FREE_RElAY_DOMAIN, \
    RELAY_STATISTIC_TYPE_FORWARDED, RELAY_STATISTIC_TYPE_BLOCKED_SPAM
from locker_server.shared.constants.relay_blacklist import RELAY_BAD_WORDS, RELAY_BLOCKLISTED, \
    RELAY_LOCKER_BLOCKED_CHARACTER
from locker_server.shared.constants.token import *
from locker_server.shared.utils.app import now, random_n_digit


UserORM = get_user_model()
RelayAddressORM = get_relay_address_model()
DeletedRelayAddressORM = get_relay_deleted_address_model()
ModelParser = get_model_parser()


class RelayAddressORMRepository(RelayAddressRepository):
    @staticmethod
    def _valid_address_pattern(address):
        # The address can't start or end with a hyphen, must be 1 - 63 lowercase alphanumeric characters
        valid_address_pattern = re.compile("^(?!-)[a-z0-9-]{1,63}(?<!-)$")
        return valid_address_pattern.match(address) is not None

    @staticmethod
    def _has_bad_words(value):
        for bad_word in RELAY_BAD_WORDS:
            bad_word = bad_word.strip()
            if len(bad_word) <= 4 and bad_word == value:
                return True
            if len(bad_word) > 4 and bad_word in value:
                return True
        return False

    @staticmethod
    def _is_blocklisted(value):
        return any(blocked_word == value for blocked_word in RELAY_BLOCKLISTED)

    @staticmethod
    def _is_locker_blocked(value):
        for blocked_word in RELAY_LOCKER_BLOCKED_CHARACTER:
            if blocked_word in value:
                return True
        return False

    # ------------------------ List RelayAddress resource ------------------- #
    def list_relay_addresses(self, **filters) -> List[RelayAddress]:
        relay_addresses_orm = RelayAddressORM.objects.all().order_by('created_time')
        subdomain_id_param = filters.get("subdomain_id")
        if subdomain_id_param:
            relay_addresses_orm = relay_addresses_orm.filter(
                subdomain_id=subdomain_id_param
            )
        return [
            ModelParser.relay_parser().parse_relay_address(relay_address_orm=relay_address_orm)
            for relay_address_orm in relay_addresses_orm
        ]

    def list_user_relay_addresses(self, user_id: int, **filters) -> List[RelayAddress]:
        relay_addresses_orm = RelayAddressORM.objects.filter(
            user_id=user_id
        ).order_by('created_time')
        return [
            ModelParser.relay_parser().parse_relay_address(relay_address_orm=relay_address_orm)
            for relay_address_orm in relay_addresses_orm
        ]

    def count_user_relay_addresses(self, user_id: int, **filters) -> int:
        user_relay_addresses_num = RelayAddressORM.objects.filter(user_id=user_id).count()
        return user_relay_addresses_num

    # ------------------------ Get RelayAddress resource --------------------- #

    def get_relay_address_by_id(self, relay_address_id: str) -> Optional[RelayAddress]:
        try:
            relay_address_orm = RelayAddressORM.objects.get(id=relay_address_id)
        except RelayAddressORM.DoesNotExist:
            return None
        return ModelParser.relay_parser().parse_relay_address(relay_address_orm=relay_address_orm)

    def get_oldest_user_relay_address(self, user_id: int) -> Optional[RelayAddress]:
        oldest_relay_address_orm = RelayAddressORM.objects.filter(user_id=user_id).order_by('created_time').first()
        if not oldest_relay_address_orm:
            return None
        return ModelParser.relay_parser().parse_relay_address(relay_address_orm=oldest_relay_address_orm)

    def get_relay_address_by_full_domain(self, address: str, domain_id: str,
                                         subdomain: str = None) -> Optional[RelayAddress]:
        try:
            if subdomain is not None:
                relay_address_orm = RelayAddressORM.objects.get(
                    address=address, domain_id=domain_id,
                    subdomain__subdomain=subdomain, subdomain__is_deleted=False
                )
            else:
                relay_address_orm = RelayAddressORM.objects.get(
                    address=address,
                    domain_id=domain_id,
                    subdomain=None
                )
        except RelayAddressORM.DoesNotExist:
            return None
        return ModelParser.relay_parser().parse_relay_address(relay_address_orm=relay_address_orm)

    def get_relay_address_by_address(self, address: str) -> Optional[RelayAddress]:
        try:
            relay_address_orm = RelayAddressORM.objects.get(address=address)
        except RelayAddressORM.DoesNotExist:
            return None
        return ModelParser.relay_parser().parse_relay_address(relay_address_orm=relay_address_orm)

    # ------------------------ Create RelayAddress resource --------------------- #
    def create_relay_address(self, relay_address_create_data) -> Optional[RelayAddress]:
        user_id = relay_address_create_data.get("user_id")
        with transaction.atomic():
            try:
                user_orm = UserORM.objects.filter(user_id=user_id).select_for_update().get()
            except UserORM.DoesNotExist:
                return None
            if relay_address_create_data.get("allow_relay_premium", False) is False and \
                    user_orm.relay_addresses.all().count() >= MAX_FREE_RElAY_DOMAIN:
                return None
            relay_address_orm = RelayAddressORM.create(**relay_address_create_data)
            return ModelParser.relay_parser().parse_relay_address(relay_address_orm=relay_address_orm)

    # ------------------------ Update RelayAddress resource --------------------- #
    def update_relay_address(self, relay_address_id: str, relay_address_update_data) -> Optional[RelayAddress]:
        try:
            relay_address_orm = RelayAddressORM.objects.get(id=relay_address_id)
        except RelayAddressORM.DoesNotExist:
            return None
        relay_address_orm.address = relay_address_update_data.get('address', relay_address_orm.address)
        relay_address_orm.enabled = relay_address_update_data.get('enabled', relay_address_orm.enabled)
        relay_address_orm.block_spam = relay_address_update_data.get('block_spam', relay_address_orm.block_spam)
        relay_address_orm.description = relay_address_update_data.get('description', relay_address_orm.description)
        relay_address_orm.num_forwarded = relay_address_update_data.get('num_forwarded',
                                                                        relay_address_orm.num_forwarded)
        relay_address_orm.num_spam = relay_address_update_data.get('num_spam', relay_address_orm.num_spam)
        relay_address_orm.num_blocked = relay_address_update_data.get('num_blocked', relay_address_orm.num_blocked)
        relay_address_orm.num_replied = relay_address_update_data.get('num_replied', relay_address_orm.num_replied)
        relay_address_orm.updated_time = relay_address_update_data.get('updated_time', now())
        relay_address_orm.save()
        return ModelParser.relay_parser().parse_relay_address(relay_address_orm=relay_address_orm)

    def update_relay_address_statistic(self, relay_address_id: str, statistic_type: str,
                                       amount: int) -> Optional[RelayAddress]:
        try:
            relay_address_orm = RelayAddressORM.objects.get(id=relay_address_id)
        except RelayAddressORM.DoesNotExist:
            return None
        if statistic_type == RELAY_STATISTIC_TYPE_FORWARDED:
            relay_address_orm.num_forwarded = F('num_forwarded') + amount
        elif statistic_type == RELAY_STATISTIC_TYPE_BLOCKED_SPAM:
            relay_address_orm.num_spam = F('num_spam') + amount
        relay_address_orm.save()
        return ModelParser.relay_parser().parse_relay_address(relay_address_orm=relay_address_orm)

    # ------------------------ Delete RelayAddress resource --------------------- #
    def delete_relay_address_by_id(self, relay_address_id: str) -> bool:
        try:
            relay_address_orm = RelayAddressORM.objects.get(id=relay_address_id)
        except RelayAddressORM.DoesNotExist:
            return False
        relay_address_orm.delete()
        return True

    def delete_subdomain_relay_addresses(self, relay_subdomain_id: str) -> bool:
        RelayAddressORM.objects.filter(subdomain_id=relay_subdomain_id).delete()
        return True
