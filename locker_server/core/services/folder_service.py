from typing import Optional, List

from locker_server.core.entities.cipher.folder import Folder
from locker_server.core.exceptions.cipher_exception import FolderDoesNotExistException
from locker_server.core.repositories.cipher_repository import CipherRepository
from locker_server.core.repositories.folder_repository import FolderRepository


class FolderService:
    """
    This class represents Use Cases related Folder
    """

    def __init__(self, folder_repository: FolderRepository, cipher_repository: CipherRepository):
        self.folder_repository = folder_repository
        self.cipher_repository = cipher_repository

    def get_by_id(self, folder_id: str) -> Optional[Folder]:
        folder = self.folder_repository.get_by_id(folder_id=folder_id)
        if not folder:
            raise FolderDoesNotExistException
        return folder

    def create_new_folder(self, user_id: int, name: str) -> Folder:
        return self.folder_repository.create_new_folder(user_id=user_id, name=name)

    def update_folder(self, user_id: int, folder_id: str, name: str) -> Folder:
        return self.folder_repository.update_folder(user_id=user_id, folder_id=folder_id, name=name)

    def destroy_folder(self, folder_id: str, user_id: int):
        # Get list ciphers in this folder then re-set folder of cipher
        ciphers = self.cipher_repository.get_multiple_by_user(user_id=user_id)
        soft_delete_cipher = []
        for cipher in ciphers:
            folders_dict = cipher.folders
            cipher_folder_id = folders_dict.get(user_id, None)
            if cipher_folder_id == folder_id:
                folders_dict.pop(user_id, None)

                self.cipher_repository.update_folders(cipher_id=cipher.cipher_id, new_folders_data=folders_dict)
                if not cipher.team:
                    soft_delete_cipher.append(cipher.cipher_id)
        # Soft delete all ciphers in folder
        self.cipher_repository.delete_multiple_cipher(cipher_ids=soft_delete_cipher, user_id_deleted=user_id)

        # Delete this folder object
        self.folder_repository.destroy_folder(folder_id=folder_id, user_id=user_id)

    def get_multiple_by_user(self, user_id: int) -> List[Folder]:
        return self.folder_repository.list_by_user_id(user_id=user_id)

    def import_multiple_folders(self, user_id: int, folders: List) -> List[str]:
        return self.folder_repository.import_multiple_folders(user_id=user_id, folders=folders)
