from abc import ABC, abstractmethod

from cystack_models.models.ciphers.folders import Folder
from cystack_models.models.users.users import User


class IFolderRepository(ABC):
    @abstractmethod
    def get_by_id(self, folder_id: str, user: User = None) -> Folder:
        pass

    @abstractmethod
    def get_multiple_by_user(self, user: User):
        pass

    @abstractmethod
    def save_new_folder(self, user: User, name: str) -> Folder:
        pass

    @abstractmethod
    def save_update_folder(self, user: User, folder: Folder, name: str) -> Folder:
        pass

    @abstractmethod
    def import_multiple_folders(self, user: User, folders):
        pass
