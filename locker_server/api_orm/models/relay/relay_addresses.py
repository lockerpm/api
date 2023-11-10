from locker_server.api_orm.abstracts.relay.relay_addresses import AbstractRelayAddressORM
from locker_server.shared.constants.relay_address import DEFAULT_RELAY_DOMAIN
from locker_server.shared.utils.app import now


class RelayAddressORM(AbstractRelayAddressORM):
    class Meta(AbstractRelayAddressORM.Meta):
        swappable = 'LS_RELAY_ADDRESS_MODEL'
        db_table = 'cs_relay_addresses'

    @classmethod
    def create(cls, **data):
        user_id = data.get('user_id')
        domain_id = data.get("domain_id") or DEFAULT_RELAY_DOMAIN
        description = data.get("description", "")
        address = data.get("address")
        subdomain_id = data.get("subdomain_id")
        new_relay_address = cls(
            user_id=user_id,
            address=address,
            domain_id=domain_id,
            subdomain_id=subdomain_id,
            created_time=now(),
            description=description,
        )
        new_relay_address.save()

        return new_relay_address
