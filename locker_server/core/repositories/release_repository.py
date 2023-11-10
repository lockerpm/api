from abc import ABC, abstractmethod
from typing import List, Optional

from locker_server.core.entities.release.release import Release


class ReleaseRepository(ABC):

    # ------------------------ List Release resource ------------------- #
    @abstractmethod
    def list_releases(self, **filters) -> List[Release]:
        pass

    # ------------------------ Get Release resource --------------------- #
    @abstractmethod
    def get_release_by_id(self, release_id: int) -> Optional[Release]:
        pass

    @abstractmethod
    def get_release(self, client_id: str, major: str, minor: str, patch: str = None, build_number: str = None):
        pass

    @abstractmethod
    def get_latest_release(self, client_id: str, environment: str) -> Optional[Release]:
        pass

    # ------------------------ Create Release resource --------------------- #
    @abstractmethod
    def create_release(self, release_create_data) -> Release:
        pass

    # ------------------------ Update Release resource --------------------- #

    # ------------------------ Delete Release resource --------------------- #
