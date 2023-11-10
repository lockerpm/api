from typing import Optional, List
from abc import ABC, abstractmethod

from locker_server.core.entities.cipher.folder import Folder


class FolderRepository(ABC):
    # ------------------------ List Folder resource ------------------- #
    @abstractmethod
    def list_by_user_id(self, user_id: int) -> List[Folder]:
        pass

    # ------------------------ Get Folder resource --------------------- #
    @abstractmethod
    def get_by_id(self, folder_id: str) -> Optional[Folder]:
        pass

    # ------------------------ Create Folder resource --------------------- #
    @abstractmethod
    def create_new_folder(self, user_id: int, name: str) -> Folder:
        pass

    @abstractmethod
    def import_multiple_folders(self, user_id: int, folders: List) -> List[str]:
        pass

    # ------------------------ Update Folder resource --------------------- #
    @abstractmethod
    def update_folder(self, user_id: int, folder_id: str, name: str) -> Folder:
        pass

    # ------------------------ Delete Folder resource --------------------- #
    @abstractmethod
    def destroy_folder(self, folder_id: str, user_id: int):
        pass
