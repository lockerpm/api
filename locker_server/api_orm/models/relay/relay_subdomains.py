from locker_server.api_orm.abstracts.relay.relay_subdomains import AbstractRelaySubdomainORM
from locker_server.shared.constants.relay_address import DEFAULT_RELAY_DOMAIN

from locker_server.shared.utils.app import now


class RelaySubdomainORM(AbstractRelaySubdomainORM):
    class Meta(AbstractRelaySubdomainORM.Meta):
        swappable = 'LS_RELAY_SUBDOMAIN_MODEL'
        db_table = 'cs_relay_subdomains'

    @classmethod
    def create_atomic(cls, user_id, subdomain: str, domain_id: str = DEFAULT_RELAY_DOMAIN, is_deleted=False):
        pass

    @classmethod
    def create(cls, **data):
        domain_id = data.get("domain_id", DEFAULT_RELAY_DOMAIN)
        is_deleted = data.get("is_deleted", False)
        relay_subdomain_orm = RelaySubdomainORM(
            user_id=data.get("user_id"),
            subdomain=data.get("subdomain"),
            domain_id=domain_id,
            created_time=data.get("created_time", now()),
            is_deleted=is_deleted,
            enabled=data.get("enabled", True),
            block_spam=data.get("block_spam", False),
            description=data.get("description"),
        )
        relay_subdomain_orm.save()
        return relay_subdomain_orm
