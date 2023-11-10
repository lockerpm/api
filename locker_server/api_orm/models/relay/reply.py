from locker_server.api_orm.abstracts.relay.reply import AbstractReplyORM

from locker_server.shared.utils.app import now


class ReplyORM(AbstractReplyORM):
    class Meta(AbstractReplyORM.Meta):
        swappable = 'LS_RELAY_REPLY_MODEL'
        db_table = 'cs_reply'

    @classmethod
    def create(cls, lookup, encrypted_metadata):
        new_reply = cls(lookup=lookup, encrypted_metadata=encrypted_metadata, created_at=now(return_float=True))
        new_reply.save()
        return new_reply
