from locker_server.api_orm.abstracts.relay.deleted_relay_addresses import AbstractDeletedRelayAddressORM


class DeletedRelayAddressORM(AbstractDeletedRelayAddressORM):
    class Meta(AbstractDeletedRelayAddressORM.Meta):
        swappable = 'LS_RELAY_DELETED_ADDRESS_MODEL'
        db_table = 'cs_deleted_relay_addresses'

    @classmethod
    def create(cls, **data):
        new_deleted_relay_address = DeletedRelayAddressORM(
            address_hash=data.get("address_hash"),
            num_forwarded=data.get("num_forwarded"),
            num_blocked=data.get("num_blocked"),
            num_replied=data.get("num_replied"),
            num_spam=data.get("num_spam"),
        )
        new_deleted_relay_address.save()
        return new_deleted_relay_address
