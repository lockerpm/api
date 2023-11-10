from locker_server.api_orm.models import *
from locker_server.core.entities.event.event import Event


class EventParser:
    @classmethod
    def parse_event(cls, event_orm: EventORM) -> Event:
        return Event(
            event_id=event_orm.id,
            event_type=event_orm.type,
            acting_user_id=event_orm.acting_user_id,
            user_id=event_orm.user_id,
            cipher_id=event_orm.cipher_id,
            collection_id=event_orm.collection_id,
            creation_date=event_orm.creation_date,
            device_type=event_orm.device_type,
            group_id=event_orm.group_id,
            ip_address=event_orm.ip_address,
            team_id=event_orm.team_id,
            team_member_id=event_orm.team_member_id,
            policy_id=event_orm.policy_id,
            provider_id=event_orm.provider_id,
            team_provider_id=event_orm.team_provider_id,
            user_provider_id=event_orm.user_provider_id,
            metadata=event_orm.get_metadata(),
        )
