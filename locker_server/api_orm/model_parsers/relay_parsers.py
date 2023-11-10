from locker_server.api_orm.model_parsers.wrapper_specific_model_parser import get_specific_model_parser
from locker_server.api_orm.models import *
from locker_server.core.entities.relay.deleted_relay_address import DeletedRelayAddress

from locker_server.core.entities.relay.relay_address import RelayAddress
from locker_server.core.entities.relay.relay_domain import RelayDomain
from locker_server.core.entities.relay.relay_subdomain import RelaySubdomain
from locker_server.core.entities.relay.reply import Reply


class RelayParser:
    @classmethod
    def parse_relay_address(cls, relay_address_orm: RelayAddressORM) -> RelayAddress:
        user_parser = get_specific_model_parser("UserParser")
        user = user_parser.parse_user(user_orm=relay_address_orm.user)
        subdomain = cls.parse_relay_subdomain(relay_subdomain_orm=relay_address_orm.subdomain) if relay_address_orm.subdomain else None
        domain = cls.parse_relay_domain(relay_domain_orm=relay_address_orm.domain)
        return RelayAddress(
            relay_address_id=relay_address_orm.id,
            user=user,
            address=relay_address_orm.address,
            subdomain=subdomain,
            domain=domain,
            enabled=relay_address_orm.enabled,
            block_spam=relay_address_orm.block_spam,
            description=relay_address_orm.description,
            created_time=relay_address_orm.created_time,
            updated_time=relay_address_orm.updated_time,
            num_forwarded=relay_address_orm.num_forwarded,
            num_blocked=relay_address_orm.num_blocked,
            num_replied=relay_address_orm.num_replied,
            num_spam=relay_address_orm.num_spam,
        )

    @classmethod
    def parse_relay_subdomain(cls, relay_subdomain_orm: RelaySubdomainORM) -> RelaySubdomain:
        user_parser = get_specific_model_parser("UserParser")
        user = user_parser.parse_user(user_orm=relay_subdomain_orm.user)
        domain = cls.parse_relay_domain(relay_domain_orm=relay_subdomain_orm.domain)
        num_alias = None
        num_spam = None
        num_forwarded = None
        if hasattr(relay_subdomain_orm, "num_alias"):
            num_alias = relay_subdomain_orm.num_alias
        if hasattr(relay_subdomain_orm, "num_spam"):
            num_spam = relay_subdomain_orm.num_spam
        if hasattr(relay_subdomain_orm, "num_forwarded"):
            num_forwarded = relay_subdomain_orm.num_forwarded

        return RelaySubdomain(
            relay_subdomain_id=relay_subdomain_orm.id,
            subdomain=relay_subdomain_orm.subdomain,
            created_time=relay_subdomain_orm.created_time,
            is_deleted=relay_subdomain_orm.is_deleted,
            user=user,
            domain=domain,
            num_alias=num_alias,
            num_spam=num_spam,
            num_forwarded=num_forwarded
        )

    @classmethod
    def parse_relay_domain(cls, relay_domain_orm: RelayDomainORM) -> RelayDomain:
        return RelayDomain(
            relay_domain_id=relay_domain_orm.id
        )

    @classmethod
    def parse_deleted_relay_address(cls, deleted_relay_address_orm: DeletedRelayAddressORM) -> DeletedRelayAddress:
        return DeletedRelayAddress(
            deleted_relay_address_id=deleted_relay_address_orm.id,
            address_hash=deleted_relay_address_orm.address_hash,
            num_forwarded=deleted_relay_address_orm.num_forwarded,
            num_blocked=deleted_relay_address_orm.num_blocked,
            num_replied=deleted_relay_address_orm.num_replied,
            num_spam=deleted_relay_address_orm.num_spam,
        )

    @classmethod
    def parse_relay_reply(cls, reply_orm: ReplyORM) -> Reply:
        return Reply(
            reply_id=reply_orm.id,
            lookup=reply_orm.lookup,
            encrypted_metadata=reply_orm.encrypted_metadata,
            created_at=reply_orm.created_at
        )
