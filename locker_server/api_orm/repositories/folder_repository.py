import uuid
from typing import Optional, List

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_folder_model, get_user_model
from locker_server.api_orm.utils.revision_date import bump_account_revision_date
from locker_server.core.entities.cipher.folder import Folder
from locker_server.core.repositories.folder_repository import FolderRepository
from locker_server.shared.utils.app import now

FolderORM = get_folder_model()
UserORM = get_user_model()
ModelParser = get_model_parser()


class FolderORMRepository(FolderRepository):
    @staticmethod
    def _get_user_orm(user_id: int) -> Optional[UserORM]:
        try:
            return UserORM.objects.get(user_id=user_id)
        except UserORM.DoesNotExist:
            return None

    # ------------------------ List Folder resource ------------------- #
    def list_by_user_id(self, user_id: int) -> List[Folder]:
        folders_orm = FolderORM.objects.filter(user_id=user_id)
        return [ModelParser.cipher_parser().parse_folder(folder_orm=folder_orm) for folder_orm in folders_orm]

    # ------------------------ Get Folder resource --------------------- #
    def get_by_id(self, folder_id: str) -> Optional[Folder]:
        try:
            folder_orm = FolderORM.objects.get(id=folder_id)
            return ModelParser.cipher_parser().parse_folder(folder_orm=folder_orm)
        except FolderORM.DoesNotExist:
            return None

    # ------------------------ Create Folder resource --------------------- #
    def create_new_folder(self, user_id: int, name: str) -> Folder:
        folder_orm = FolderORM(
            name=name, user_id=user_id, creation_date=now(), revision_date=now()
        )
        folder_orm.save()
        bump_account_revision_date(user=folder_orm.user)
        return ModelParser.cipher_parser().parse_folder(folder_orm=folder_orm)

    def import_multiple_folders(self, user_id: int, folders: List) -> List[str]:
        folder_ids = []
        import_folders = []
        existed_folder_ids = list(FolderORM.objects.filter(user_id=user_id).values_list('id', flat=True))
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
            import_folders.append(FolderORM(
                id=folder["id"], name=folder["name"], user_id=user_id, creation_date=now(), revision_date=now()
            ))
        FolderORM.objects.bulk_create(import_folders, batch_size=100, ignore_conflicts=True)
        bump_account_revision_date(user=self._get_user_orm(user_id=user_id))

        return folder_ids

    # ------------------------ Update Folder resource --------------------- #
    def update_folder(self, user_id: int, folder_id: str, name: str) -> Folder:
        try:
            folder_orm = FolderORM.objects.get(id=folder_id)
        except FolderORM.DoesNotExist:
            return None
        folder_orm.user_id = user_id
        folder_orm.name = name
        folder_orm.revision_date = now()
        folder_orm.save()
        bump_account_revision_date(user=folder_orm.user)
        return ModelParser.cipher_parser().parse_folder(folder_orm=folder_orm)

    # ------------------------ Delete Folder resource --------------------- #
    def destroy_folder(self, folder_id: str, user_id: int):
        try:
            folder_orm = FolderORM.objects.get(id=folder_id, user_id=user_id)
            folder_orm.delete()
            return True
        except FolderORM.DoesNotExist:
            return False
