from locker_server.api_orm.abstracts.relay.relay_domains import AbstractRelayDomainORM


class RelayDomainORM(AbstractRelayDomainORM):
    class Meta(AbstractRelayDomainORM.Meta):
        swappable = 'LS_RELAY_DOMAIN_MODEL'
        db_table = 'cs_relay_domains'
