from typing import Optional, List

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_relay_reply_model

from locker_server.core.entities.relay.reply import Reply
from locker_server.core.repositories.relay_repositories.reply_repository import ReplyRepository

ReplyORM = get_relay_reply_model()
ModelParser = get_model_parser()


class ReplyORMRepository(ReplyRepository):
    # ------------------------ List Reply resource ------------------- #
    def list_replies(self, **filters) -> List[Reply]:
        replies_orm = ReplyORM.objects.all().order_by('created_at')
        return [
            ModelParser.relay_parser().parse_relay_reply(reply_orm=reply_orm)
            for reply_orm in replies_orm
        ]

    # ------------------------ Get Reply resource --------------------- #
    def get_reply_by_id(self, reply_id: str) -> Optional[Reply]:
        try:
            reply_orm = ReplyORM.objects.get(id=reply_id)
        except ReplyORM.DoesNotExist:
            return None
        return ModelParser.relay_parser().parse_relay_reply(reply_orm=reply_orm)

    def get_reply_by_lookup(self, lookup: str) -> Optional[Reply]:
        try:
            reply_orm = ReplyORM.objects.get(lookup=lookup)
        except ReplyORM.DoesNotExist:
            return None
        return ModelParser.relay_parser().parse_relay_reply(reply_orm=reply_orm)

    # ------------------------ Create Reply resource --------------------- #
    def create_reply(self, **reply_create_data) -> Reply:
        new_reply_orm = ReplyORM.create(**reply_create_data)
        return ModelParser.relay_parser().parse_relay_reply(reply_orm=new_reply_orm)

    # ------------------------ Update Reply resource --------------------- #

    # ------------------------ Delete Reply resource --------------------- #
