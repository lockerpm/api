from core.repositories import IFolderRepository

from cystack_models.models.users.users import User
from cystack_models.models.ciphers.folders import Folder
from shared.utils.app import now


class FolderRepository(IFolderRepository):
    def get_by_id(self, folder_id: str, user: User = None) -> Folder:
        if user:
            folder = Folder.objects.get(id=folder_id, user=user)
        else:
            folder = Folder.objects.get(id=folder_id)
        return folder

    def get_multiple_by_user(self, user: User):
        folders = Folder.objects.filter(user=user)
        return folders

    def save_new_folder(self, user: User, name: str) -> Folder:
        folder = Folder(
            name=name, user=user, creation_date=now(), revision_date=now()
        )
        folder.save()
        user.revision_date = now()
        user.save()
        return folder

    def save_update_folder(self, user: User, folder: Folder, name: str) -> Folder:
        folder.user = user
        folder.name = name
        folder.revision_date = now()
        folder.save()
        return folder
