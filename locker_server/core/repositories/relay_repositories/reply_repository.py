from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.relay.reply import Reply


class ReplyRepository(ABC):
    # ------------------------ List Reply resource ------------------- #
    @abstractmethod
    def list_replies(self, **filters) -> List[Reply]:
        pass

    # ------------------------ Get Reply resource --------------------- #
    @abstractmethod
    def get_reply_by_id(self, reply_id: str) -> Optional[Reply]:
        pass

    @abstractmethod
    def get_reply_by_lookup(self, lookup: str) -> Optional[Reply]:
        pass

    # ------------------------ Create Reply resource --------------------- #
    @abstractmethod
    def create_reply(self, **reply_create_data) -> Reply:
        pass

    # ------------------------ Update Reply resource --------------------- #

    # ------------------------ Delete Reply resource --------------------- #
