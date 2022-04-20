import uuid

from core.repositories import IFolderRepository
from core.utils.account_revision_date import bump_account_revision_date

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
        bump_account_revision_date(user=folder.user)
        return folder

    def save_update_folder(self, user: User, folder: Folder, name: str) -> Folder:
        folder.user = user
        folder.name = name
        folder.revision_date = now()
        folder.save()
        bump_account_revision_date(user=folder.user)
        return folder

    def import_multiple_folders(self, user: User, folders):
        folder_ids = []
        import_folders = []
        existed_folder_ids = list(user.folders.values_list('id', flat=True))
        # Init id for folders
        for folder in folders:
            while True:
                new_folder_id = str(uuid.uuid4())
                if new_folder_id not in existed_folder_ids:
                    break
            folder["id"] = new_folder_id
            folder_ids.append(new_folder_id)
        # Create folders
        for folder in folders:
            import_folders.append(
                Folder(id=folder["id"], name=folder["name"], user=user, creation_date=now(), revision_date=now())
            )
        Folder.objects.bulk_create(import_folders, batch_size=100, ignore_conflicts=True)
        bump_account_revision_date(user=user)

        return folder_ids
