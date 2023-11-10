from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.cipher.cipher import Cipher
from locker_server.core.entities.cipher.folder import Folder
from locker_server.core.entities.member.team_member import TeamMember
from locker_server.core.entities.team.collection import Collection
from locker_server.core.entities.user.device import Device
from locker_server.core.entities.user.user import User


class CollectionRepository(ABC):
    # ------------------------ List Collection resource ------------------- #
    @abstractmethod
    def list_user_collections(self, user_id: int, exclude_team_ids=None, filter_ids=None) -> List[Collection]:
        pass

    # ------------------------ Get Collection resource --------------------- #
    @abstractmethod
    def get_by_id(self, collection_id: str) -> Optional[Collection]:
        pass

    # ------------------------ Create Collection resource --------------------- #

    # ------------------------ Update Collection resource --------------------- #

    # ------------------------ Delete Collection resource --------------------- #
