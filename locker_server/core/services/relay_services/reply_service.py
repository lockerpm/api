from typing import Optional

from locker_server.core.entities.relay.reply import Reply
from locker_server.core.exceptions.relay_exceptions.reply_exception import ReplyDoesNotExistException, \
    ReplyLookupExistedException
from locker_server.core.repositories.relay_repositories.reply_repository import ReplyRepository


class ReplyService:
    """
    This class represents Use Cases related relay hook
    """

    def __init__(self, reply_repository: ReplyRepository):
        self.reply_repository = reply_repository

    def get_reply_by_lookup(self, lookup: str) -> Optional[Reply]:
        reply = self.reply_repository.get_reply_by_lookup(lookup=lookup)
        if not reply:
            raise ReplyDoesNotExistException
        return reply

    def create_reply(self, lookup: str, encrypted_metadata: str) -> Reply:
        existed_reply = self.get_reply_by_lookup(lookup=lookup)
        if existed_reply:
            raise ReplyLookupExistedException
        new_reply = self.reply_repository.create_reply(**{
            "lookup": lookup,
            "encrypted_metadata": encrypted_metadata
        })
        return new_reply
