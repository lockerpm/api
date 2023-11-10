from locker_server.api_orm.abstracts.events.events import AbstractEventORM


class EventORM(AbstractEventORM):
    class Meta(AbstractEventORM.Meta):
        swappable = 'LS_EVENT_MODEL'
        db_table = 'cs_events'
