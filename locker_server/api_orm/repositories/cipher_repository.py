import json
import uuid
from typing import Union, Dict, Optional, List
from abc import ABC, abstractmethod

from django.db.models import Value, BooleanField, Q, Case, When, Count, F

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_cipher_model, get_folder_model, get_collection_cipher_model, \
    get_team_model, get_collection_member_model, get_team_member_model, get_user_model
from locker_server.api_orm.utils.revision_date import bump_account_revision_date
from locker_server.core.entities.cipher.cipher import Cipher
from locker_server.core.entities.cipher.folder import Folder
from locker_server.core.entities.member.team_member import TeamMember
from locker_server.core.entities.user.device import Device
from locker_server.core.entities.user.user import User
from locker_server.core.repositories.cipher_repository import CipherRepository
from locker_server.shared.constants.ciphers import *
from locker_server.shared.constants.members import *
from locker_server.shared.utils.app import now, diff_list, get_cipher_detail_data

UserORM = get_user_model()
TeamORM = get_team_model()
TeamMemberORM = get_team_member_model()
CipherORM = get_cipher_model()
CollectionCipherORM = get_collection_cipher_model()
CollectionMemberORM = get_collection_member_model()
FolderORM = get_folder_model()
ModelParser = get_model_parser()


class CipherORMRepository(CipherRepository):
    @staticmethod
    def _get_cipher_orm(cipher_id: str) -> Optional[CipherORM]:
        try:
            cipher_orm = CipherORM.objects.get(id=cipher_id)
            return cipher_orm
        except CipherORM.DoesNotExist:
            return None

    @staticmethod
    def _get_user_orm(user_id: int) -> Optional[UserORM]:
        try:
            user_orm = UserORM.objects.get(user_id=user_id)
            return user_orm
        except UserORM.DoesNotExist:
            return None

    @staticmethod
    def _get_multiple_ciphers_orm_by_user(user_id: int, only_personal=False, only_managed_team=False,
                                          only_edited=False, only_deleted=False,
                                          exclude_team_ids=None, filter_ids=None, exclude_types=None):
        """
        Get list ciphers of user
        :param user_id: (int) The user id
        :param only_personal: (bool) if True => Only get list personal ciphers
        :param only_managed_team: (bool) if True => Only get list ciphers of non-locked teams
        :param only_edited: (bool) if True => Only get list ciphers that user is allowed edit permission
        :param only_deleted: (bool) if True => Only get list ciphers that user is allowed delete permission
        :param exclude_team_ids: (list) Excluding all ciphers have team_id in this list
        :param filter_ids: (list) List filtered cipher ids
        :param exclude_types: (list) Excluding all ciphers have type in this list
        :return:
        """
        if exclude_types is None:
            exclude_types = []
        personal_ciphers_orm = CipherORM.objects.filter(user_id=user_id)
        if filter_ids:
            personal_ciphers_orm = personal_ciphers_orm.filter(id__in=filter_ids)
        if only_personal is True:
            personal_ciphers_orm = personal_ciphers_orm.annotate(view_password=Value(True, output_field=BooleanField()))
            return personal_ciphers_orm

        confirmed_team_members_orm = TeamMemberORM.objects.filter(user_id=user_id, status=PM_MEMBER_STATUS_CONFIRMED)
        if only_managed_team:
            confirmed_team_members_orm = confirmed_team_members_orm.filter(team__locked=False)
        if exclude_team_ids:
            confirmed_team_members_orm = confirmed_team_members_orm.exclude(team_id__in=exclude_team_ids)

        confirmed_team_ids = confirmed_team_members_orm.values_list('team_id', flat=True)
        team_ciphers_orm = CipherORM.objects.filter(team_id__in=confirmed_team_ids)
        if filter_ids:
            team_ciphers_orm = team_ciphers_orm.filter(id__in=filter_ids)

        team_ciphers_orm = team_ciphers_orm.filter(
            # Owner, Admin ciphers
            Q(
                team__team_members__role_id__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN],
                team__team_members__user_id=user_id
            ) |
            # Group access all ciphers
            Q(
                team__groups__access_all=True,
                team__groups__groups_members__member__user_id=user_id
            ) |
            # Team member
            Q(
                collections_ciphers__collection__collections_members__member__in=confirmed_team_members_orm,
                team__team_members__user_id=user_id
            ) |
            # Q(
            #     collections_ciphers__collection__collections_groups__group__groups_members__member__in=confirmed_team_members,
            #     team__team_members__user=user
            # ) |
            # Personal share
            Q(
                team__personal_share=True,
                team__team_members__user_id=user_id
            )
        ).distinct().annotate(
            view_password=Case(
                When(
                    Q(
                        team__team_members__role_id__in=[MEMBER_ROLE_MEMBER],
                        team__team_members__user_id=user_id,
                        collections_ciphers__collection__collections_members__hide_passwords=True
                    ), then=False
                ),
                When(
                    Q(
                        team__team_members__role_id__in=[MEMBER_ROLE_MEMBER],
                        team__team_members__user_id=user_id,
                        team__personal_share=True,
                        team__team_members__hide_passwords=True
                    ), then=False
                ),
                default=True,
                output_field=BooleanField()
            )
        )
        hide_password_cipher_ids = team_ciphers_orm.filter(view_password=False).values_list('id', flat=True)
        if only_edited:
            team_ciphers_orm = team_ciphers_orm.filter(
                team__team_members__role_id__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER],
                team__team_members__user_id=user_id
            )
        if only_deleted:
            team_ciphers_orm = team_ciphers_orm.filter(
                team__team_members__role_id__in=[MEMBER_ROLE_OWNER],
                team__team_members__user_id=user_id
            )
        return CipherORM.objects.filter(
            id__in=list(
                personal_ciphers_orm.values_list('id', flat=True)
            ) + list(team_ciphers_orm.values_list('id', flat=True))
        ).exclude(type__in=exclude_types).annotate(
            view_password=Case(
                When(id__in=hide_password_cipher_ids, then=False),
                default=True,
                output_field=BooleanField()
            )
        ).order_by('-revision_date')  # .prefetch_related('collections_ciphers')

    # ------------------------ List Cipher resource ------------------- #
    def list_cipher_collection_ids(self, cipher_id: str) -> List[str]:
        return list(CollectionCipherORM.objects.filter(cipher_id=cipher_id).values_list('collection_id', flat=True))

    def get_multiple_by_user(self, user_id: int, only_personal=False, only_managed_team=False,
                             only_edited=False, only_deleted=False,
                             exclude_team_ids=None, filter_ids=None, exclude_types=None) -> List[Cipher]:
        """
        Get list ciphers of user
        :param user_id: (int) The user id
        :param only_personal: (bool) if True => Only get list personal ciphers
        :param only_managed_team: (bool) if True => Only get list ciphers of non-locked teams
        :param only_edited: (bool) if True => Only get list ciphers that user is allowed edit permission
        :param only_deleted: (bool) if True => Only get list ciphers that user is allowed delete permission
        :param exclude_team_ids: (list) Excluding all ciphers have team_id in this list
        :param filter_ids: (list) List filtered cipher ids
        :param exclude_types: (list) Excluding all ciphers have type in this list
        :return:
        """

        ciphers_orm = self._get_multiple_ciphers_orm_by_user(
            user_id=user_id, only_personal=only_personal, only_managed_team=only_managed_team,
            only_edited=only_edited, only_deleted=only_deleted,
            exclude_team_ids=exclude_team_ids, filter_ids=filter_ids, exclude_types=exclude_types
        ).prefetch_related('collections_ciphers')
        return [ModelParser.cipher_parser().parse_cipher(cipher_orm=c, parse_collection_ids=True) for c in ciphers_orm]

    def get_ciphers_created_by_user(self, user_id: int) -> List[Cipher]:
        ciphers_orm = CipherORM.objects.filter(created_by_id=user_id)
        return [ModelParser.cipher_parser().parse_cipher(cipher_orm=c) for c in ciphers_orm]

    def get_cipher_ids_created_by_user(self, user_id: int) -> List[str]:
        return list(CipherORM.objects.filter(created_by_id=user_id).values_list('id', flat=True))

    def get_multiple_by_ids(self, cipher_ids: List[str]) -> List[Cipher]:
        ciphers_orm = CipherORM.objects.filter(id__in=cipher_ids).select_related('team')
        return [ModelParser.cipher_parser().parse_cipher(cipher_orm=c) for c in ciphers_orm]

    def list_cipher_ids_by_folder_id(self, user_id: int, folder_id: str) -> List[str]:
        return list(CipherORM.objects.filter(user_id=user_id).filter(
            Q(folders__icontains="{}: '{}'".format(user_id, folder_id)) |
            Q(folders__icontains='{}: "{}"'.format(user_id, folder_id))
        ).values_list('id', flat=True))

    def list_cipher_ids_by_collection_id(self, collection_id: str) -> List[str]:
        return list(CollectionCipherORM.objects.filter(collection_id=collection_id).values_list('cipher_id', flat=True))

    # ------------------------ Get Cipher resource --------------------- #
    def get_by_id(self, cipher_id: str) -> Optional[Cipher]:
        cipher_orm = self._get_cipher_orm(cipher_id=cipher_id)
        if not cipher_orm:
            return None
        return ModelParser.cipher_parser().parse_cipher(cipher_orm=cipher_orm)

    def get_user_folder(self, user_id: int, folder_id: str) -> Optional[Folder]:
        try:
            folder_orm = FolderORM.objects.get(user_id=user_id, id=folder_id)
        except FolderORM.DoesNotExist:
            return None
        return ModelParser.cipher_parser().parse_folder(folder_orm=folder_orm)

    def count_ciphers_created_by_user(self, user_id: int, **filter_params) -> int:
        ciphers = CipherORM.objects.filter(created_by_id=user_id)
        type_param = filter_params.get("type")
        if type_param:
            ciphers = ciphers.filter(type=type_param)
        return ciphers.count()

    def get_master_pwd_item(self, user_id: int) -> Optional[Cipher]:
        master_pwd_item = CipherORM.objects.filter(created_by_id=user_id, type=CIPHER_TYPE_MASTER_PASSWORD).first()
        return ModelParser.cipher_parser().parse_cipher(cipher_orm=master_pwd_item) if master_pwd_item else None

    def check_member_belongs_cipher_collections(self, cipher: Cipher, member: TeamMember) -> bool:
        cipher_collection_ids = self.list_cipher_collection_ids(cipher_id=cipher.cipher_id)
        member_collection_ids = list(
            CollectionMemberORM.objects.filter(member_id=member.team_member_id).values_list('collection_id', flat=True)
        )
        return any(collection_id in cipher_collection_ids for collection_id in member_collection_ids)

    def sync_and_statistic_ciphers(self, user_id: int, only_personal=False, only_managed_team=False,
                                   only_edited=False, only_deleted=False,
                                   exclude_team_ids=None, filter_ids=None, exclude_types=None) -> Dict:
        ciphers_orm = self._get_multiple_ciphers_orm_by_user(
            user_id=user_id, only_personal=only_personal, only_managed_team=only_managed_team,
            only_edited=only_edited, only_deleted=only_deleted,
            exclude_team_ids=exclude_team_ids, filter_ids=filter_ids, exclude_types=exclude_types
        ).select_related('user').select_related('created_by').select_related('team').prefetch_related(
            'collections_ciphers'
        )
        total_cipher = ciphers_orm.count()
        not_deleted_ciphers_orm = ciphers_orm.filter(deleted_date__isnull=True)
        not_deleted_ciphers_statistic = not_deleted_ciphers_orm.values('type').annotate(
            count=Count('type')
        ).order_by('-count')
        not_deleted_ciphers_count = {item["type"]: item["count"] for item in list(not_deleted_ciphers_statistic)}
        return {
            "count": {
                "ciphers": total_cipher,
                "not_deleted_ciphers": {
                    "total": not_deleted_ciphers_orm.count(),
                    "ciphers": not_deleted_ciphers_count
                },
            },
            "ciphers": [
                ModelParser.cipher_parser().parse_cipher(cipher_orm=c, parse_collection_ids=True) for c in ciphers_orm
            ]
        }

    def statistic_created_ciphers(self, user_id: int) -> Dict:
        ciphers_statistic = CipherORM.objects.filter(created_by_id=user_id)
        ciphers_statistic_data = {
            "total": ciphers_statistic.count(),
            CIPHER_TYPE_LOGIN: ciphers_statistic.filter(type=CIPHER_TYPE_LOGIN).count(),
            CIPHER_TYPE_NOTE: ciphers_statistic.filter(type=CIPHER_TYPE_NOTE).count(),
            CIPHER_TYPE_IDENTITY: ciphers_statistic.filter(type=CIPHER_TYPE_IDENTITY).count(),
            CIPHER_TYPE_CARD: ciphers_statistic.filter(type=CIPHER_TYPE_CARD).count(),
            CIPHER_TYPE_TOTP: ciphers_statistic.filter(type=CIPHER_TYPE_TOTP).count(),
            CIPHER_TYPE_CRYPTO_WALLET: ciphers_statistic.filter(type=CIPHER_TYPE_CRYPTO_WALLET).count(),
        }
        return ciphers_statistic_data

    # ------------------------ Create Cipher resource --------------------- #
    def create_cipher(self, cipher_data: Dict) -> Cipher:
        favorite = cipher_data.get("favorite", False)
        folder_id = cipher_data.get("folder_id", None)
        user_created_id = cipher_data.get("user_id")
        created_by_id = cipher_data.get("created_by_id")
        user_cipher_id = cipher_data.get("user_id")
        team_id = cipher_data.get("team_id")
        collection_ids = cipher_data.get("collection_ids", [])
        # If team_id is not null => This cipher belongs to team
        if team_id:
            user_cipher_id = None
        # Create new cipher object
        cipher_orm = CipherORM(
            creation_date=cipher_data.get("creation_date", now()),
            revision_date=cipher_data.get("revision_date", now()),
            deleted_date=cipher_data.get("deleted_date"),
            reprompt=cipher_data.get("reprompt", 0) or 0,
            score=cipher_data.get("score", 0),
            type=cipher_data.get("type"),
            data=cipher_data.get("data"),
            user_id=user_cipher_id,
            team_id=team_id,
            created_by_id=created_by_id,
        )
        cipher_orm.save()
        # Create CipherFavorite
        if user_created_id and favorite:
            cipher_orm.set_favorite(user_created_id, True)
        # Create CipherFolder
        if user_created_id and folder_id:
            cipher_orm.set_folder(user_created_id, folder_id)
        # Create CipherCollections
        if team_id:
            cipher_orm.collections_ciphers.model.create_multiple(cipher_orm.id, *collection_ids)

        # Update revision date of user (if this cipher is personal)
        # or all related cipher members (if this cipher belongs to a team)
        bump_account_revision_date(team=cipher_orm.team, **{
            "collection_ids": collection_ids,
            "role_name": [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]
        })
        bump_account_revision_date(user=cipher_orm.user)
        return ModelParser.cipher_parser().parse_cipher(cipher_orm=cipher_orm)

    def sync_personal_cipher_offline(self, user_id: int, ciphers: List, folders: List, folder_relationships: List):
        user_orm = self._get_user_orm(user_id=user_id)
        # Init id for folders
        existed_folder_ids = list(FolderORM.objects.filter(user=user_orm).values_list('id', flat=True))
        for folder in folders:
            if not folder.get("id"):
                while True:
                    new_folder_id = str(uuid.uuid4())
                    if new_folder_id not in existed_folder_ids:
                        break
                folder["id"] = new_folder_id

        # Create the folder associations based on the newly created folder ids
        for folder_relationship in folder_relationships:
            try:
                cipher = ciphers[folder_relationship["key"]]
                folder = folders[folder_relationship["value"]]
            except (KeyError, ValueError):
                continue

            cipher["folders"] = "{%d: '%s'}" % (user_orm.user_id, folder.get("id"))

        # Create multiple folders
        sync_folders = []
        for folder in folders:
            sync_folders.append(
                FolderORM(id=folder["id"], name=folder["name"], user=user_orm, creation_date=now(), revision_date=now())
            )
        FolderORM.objects.bulk_create(sync_folders, batch_size=100, ignore_conflicts=True)

        # Create multiple ciphers
        sync_create_ciphers = []
        sync_create_ciphers_data = [
            cipher_data for cipher_data in ciphers if
            not cipher_data.get("id") and cipher_data.get("type") != CIPHER_TYPE_MASTER_PASSWORD
        ]
        for cipher_data in sync_create_ciphers_data:
            # Only allow sync personal ciphers
            if cipher_data.get("organizationId") or cipher_data.get("team"):
                continue
            # Get cipher data
            cipher_data["data"] = get_cipher_detail_data(cipher=cipher_data)
            cipher_data = json.loads(json.dumps(cipher_data))
            sync_create_ciphers.append(
                CipherORM(
                    creation_date=cipher_data.get("creationDate", now()),
                    revision_date=cipher_data.get("revisionDate", now()),
                    deleted_date=cipher_data.get("deletedDate"),
                    reprompt=cipher_data.get("reprompt", 0) or 0,
                    score=cipher_data.get("score", 0),
                    type=cipher_data.get("type"),
                    data=cipher_data.get("data"),
                    user_id=user_orm.user_id,
                    folders=cipher_data.get("folders", ""),
                    team_id=cipher_data.get("organizationId")
                )
            )

        CipherORM.objects.bulk_create(sync_create_ciphers, batch_size=100, ignore_conflicts=True)

        # Sync update existed ciphers
        sync_update_ciphers = []
        sync_update_ciphers_data = [
            cipher_data for cipher_data in ciphers if
            cipher_data.get("id") and cipher_data.get("type") != CIPHER_TYPE_MASTER_PASSWORD
        ]
        sync_update_cipher_ids = [cipher_data.get("id") for cipher_data in sync_update_ciphers_data]
        user_update_ciphers_orm = user_orm.ciphers.filter(id__in=sync_update_cipher_ids)
        user_update_ciphers_dict = {}
        for cipher_orm in user_update_ciphers_orm:
            user_update_ciphers_dict[cipher_orm.id] = cipher_orm
        for cipher_data in sync_update_ciphers_data:
            # Only allow sync personal ciphers
            if cipher_data.get("organizationId") or cipher_data.get("team"):
                continue
            cipher_obj = user_update_ciphers_dict.get(cipher_data.get("id"))
            cipher_type = cipher_data.get("type")
            if cipher_type == CIPHER_TYPE_LOGIN:
                cipher_data["data"] = dict(cipher_data.get("login"))
            elif cipher_type == CIPHER_TYPE_CARD:
                cipher_data["data"] = dict(cipher_data.get("card"))
            elif cipher_type == CIPHER_TYPE_IDENTITY:
                cipher_data["data"] = dict(cipher_data.get("identity"))
            elif cipher_type == CIPHER_TYPE_NOTE:
                cipher_data["data"] = dict(cipher_data.get("secureNote"))
            elif cipher_type == CIPHER_TYPE_TOTP:
                cipher_data["data"] = dict(cipher_data.get("secureNote"))
            cipher_data["data"]["name"] = cipher_data.get("name")
            if cipher_data.get("notes"):
                cipher_data["data"]["notes"] = cipher_data.get("notes")
            cipher_data = json.loads(json.dumps(cipher_data))

            cipher_obj.creation_date = cipher_data.get("creationDate", now())
            cipher_obj.revision_date = cipher_data.get("revisionDate", now())
            cipher_obj.deleted_date = cipher_data.get("deletedDate")
            cipher_obj.reprompt = cipher_data.get("reprompt", 0) or 0
            cipher_obj.score = cipher_data.get("score", 0)
            cipher_obj.type = cipher_data.get("type")
            cipher_obj.data = cipher_data.get("data")
            cipher_obj.user_id = user_orm.user_id
            cipher_obj.folders = cipher_data.get("folders", "")
            cipher_obj.team_id = cipher_data.get("organizationId")
            sync_update_ciphers.append(cipher_obj)

        CipherORM.objects.bulk_update(
            sync_update_ciphers,
            ['creation_date', 'revision_date', 'deleted_date', 'reprompt', 'score', 'type',
             'data', 'user_id', 'folders', 'team_id'],
            batch_size=100
        )
        bump_account_revision_date(user=user_orm)

    def import_multiple_ciphers(self, user: User, ciphers: List, allow_cipher_type: Dict = None):
        user_id = user.user_id
        user_orm = self._get_user_orm(user_id=user_id)
        existed_folder_ids = list(user_orm.folders.values_list('id', flat=True))

        # Check limit ciphers
        existed_ciphers_orm = CipherORM.objects.filter(created_by_id=user_id).values('type').annotate(
            count=Count('type')
        )
        existed_ciphers_count = {item["type"]: item["count"] for item in list(existed_ciphers_orm)}

        # Create multiple ciphers
        import_ciphers = []
        import_ciphers_count = {vault_type: 0 for vault_type in LIST_CIPHER_TYPE}

        for cipher_data in ciphers:
            # Only accepts ciphers which have name
            if not cipher_data.get("name"):
                continue
            cipher_type = cipher_data.get("type")

            # Check limit ciphers
            if allow_cipher_type and allow_cipher_type.get(cipher_type) and import_ciphers_count.get(cipher_type, 0) + \
                    existed_ciphers_count.get(cipher_type, 0) >= allow_cipher_type.get(cipher_type):
                continue
            import_ciphers_count[cipher_type] = import_ciphers_count.get(cipher_type) + 1

            # Get folder id
            folder_id = None
            if cipher_data.get("folderId") and cipher_data.get("folderId") in existed_folder_ids:
                folder_id = cipher_data.get("folderId")
            folders = "{%d: '%s'}" % (user.user_id, folder_id) if folder_id else ""

            # Get cipher data
            cipher_data["data"] = get_cipher_detail_data(cipher=cipher_data)
            cipher_data = json.loads(json.dumps(cipher_data))
            import_ciphers.append(
                CipherORM(
                    creation_date=cipher_data.get("creation_date", now()),
                    revision_date=cipher_data.get("revision_date", now()),
                    deleted_date=cipher_data.get("deleted_date"),
                    reprompt=cipher_data.get("reprompt", 0) or 0,
                    score=cipher_data.get("score", 0),
                    type=cipher_data.get("type"),
                    data=cipher_data.get("data"),
                    user_id=user_id,
                    created_by_id=user_id,
                    folders=folders,
                    team_id=cipher_data.get("organizationId")
                )
            )
        CipherORM.objects.bulk_create(import_ciphers, batch_size=100, ignore_conflicts=True)
        bump_account_revision_date(user=user_orm)

    # ------------------------ Update Cipher resource --------------------- #
    def update_cipher(self, cipher_id: str, cipher_data: Dict) -> Cipher:
        cipher_orm = self._get_cipher_orm(cipher_id=cipher_id)
        user_created_id = cipher_data.get("user_id")
        user_cipher_id = cipher_data.get("user_id")
        team_id = cipher_data.get("team_id")
        collection_ids = cipher_data.get("collection_ids", [])

        # If team_id is not null => This cipher belongs to team
        if team_id:
            user_cipher_id = None
        # Create new cipher object
        cipher_orm.revision_date = now()
        cipher_orm.reprompt = cipher_data.get("reprompt", cipher_orm.reprompt) or 0
        cipher_orm.score = cipher_data.get("score", cipher_orm.score)
        cipher_orm.type = cipher_data.get("type", cipher_orm.type)
        cipher_orm.data = cipher_data.get("data", cipher_orm.get_data())
        cipher_orm.user_id = user_cipher_id
        cipher_orm.team_id = team_id
        cipher_orm.save()
        # Set favorite
        if user_created_id:
            favorite = cipher_data.get("favorite", cipher_orm.get_favorites().get(user_created_id, False))
            cipher_orm.set_favorite(user_id=user_created_id, is_favorite=favorite)

        # Set folder id
        folder_id = cipher_data.get("folder_id", cipher_orm.get_folders().get(user_created_id))
        cipher_orm.set_folder(user_created_id, folder_id)
        # Create CipherCollections
        if team_id:
            existed_collection_ids = list(cipher_orm.collections_ciphers.values_list('collection_id', flat=True))
            removed_collection_ids = diff_list(existed_collection_ids, collection_ids)
            added_collection_ids = diff_list(collection_ids, existed_collection_ids)
            cipher_orm.collections_ciphers.filter(collection_id__in=removed_collection_ids).delete()
            cipher_orm.collections_ciphers.model.create_multiple(cipher_orm.id, *added_collection_ids)
        else:
            cipher_orm.collections_ciphers.all().delete()

        # Update revision date of user (if this cipher is personal)
        # or all related cipher members (if this cipher belongs to a team)
        bump_account_revision_date(team=cipher_orm.team, **{
            "collection_ids": collection_ids,
            "role_name": [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]
        })
        bump_account_revision_date(user=cipher_orm.user)

        return ModelParser.cipher_parser().parse_cipher(cipher_orm=cipher_orm)

    def update_folders(self, cipher_id: str, new_folders_data) -> Cipher:
        cipher_orm = self._get_cipher_orm(cipher_id=cipher_id)
        cipher_orm.folders = new_folders_data
        cipher_orm.save()
        return ModelParser.cipher_parser().parse_cipher(cipher_orm=cipher_orm)

    def update_cipher_use(self, cipher_id: str, cipher_use_data: Dict) -> Cipher:
        cipher_orm = self._get_cipher_orm(cipher_id=cipher_id)
        if not cipher_orm:
            return None

        user_id = cipher_use_data.get("user_id")
        # Set favorite
        if user_id:
            favorite = cipher_use_data.get("favorite", cipher_orm.get_favorites().get(user_id, False))
            cipher_orm.set_favorite(user_id=user_id, is_favorite=favorite)
        # Set last_use_date, num_use
        if cipher_use_data.get("use"):
            cipher_orm.last_use_date = cipher_use_data.get("last_use_date", now(return_float=True))
            cipher_orm.num_use = F('num_use') + 1
        cipher_orm.save()
        cipher_orm.refresh_from_db()
        # Update revision date
        bump_account_revision_date(team=cipher_orm.team)
        bump_account_revision_date(user=cipher_orm.user)
        return ModelParser.cipher_parser().parse_cipher(cipher_orm=cipher_orm)

    def move_multiple_cipher(self, cipher_ids: List[str], user_id_moved: int, folder_id: str) -> List[str]:
        # Filter list ciphers of users
        ciphers_orm = self._get_multiple_ciphers_orm_by_user(
            user_id=user_id_moved
        ).filter(
            id__in=cipher_ids, deleted_date__isnull=True
        ).exclude(type__in=IMMUTABLE_CIPHER_TYPES)
        moved_cipher_ids = []
        for cipher_orm in ciphers_orm:
            cipher_orm.set_folder(user_id=user_id_moved, folder_id=folder_id)
            moved_cipher_ids.append(cipher_orm.id)
        # Bump revision date of user
        bump_account_revision_date(user=self._get_user_orm(user_id=user_id_moved))
        return moved_cipher_ids

    # ------------------------ Delete Cipher resource --------------------- #
    def delete_permanent_multiple_cipher_by_teams(self, team_ids):
        """
        Delete permanently ciphers by team ids
        :param team_ids:
        :return:
        """
        teams_orm = TeamORM.objects.filter(id__in=team_ids)
        CipherORM.objects.filter(team_id__in=team_ids).delete()
        for team_orm in teams_orm:
            bump_account_revision_date(team=team_orm)

    def delete_permanent_multiple_cipher(self, cipher_ids: List[str], user_id_deleted: int) -> List[str]:
        ciphers_orm = self._get_multiple_ciphers_orm_by_user(user_id=user_id_deleted, only_deleted=True).filter(
            id__in=cipher_ids
        ).exclude(type__in=IMMUTABLE_CIPHER_TYPES)
        team_ids = ciphers_orm.exclude(team__isnull=True).values_list('team_id', flat=True)
        # Delete ciphers objects
        deleted_cipher_ids = list(ciphers_orm.values_list('id', flat=True))
        ciphers_orm.delete()
        # Bump revision date: teams and user
        teams_orm = TeamORM.objects.filter(id__in=team_ids)
        for team_orm in teams_orm:
            bump_account_revision_date(team=team_orm)
        bump_account_revision_date(user=self._get_user_orm(user_id=user_id_deleted))
        return deleted_cipher_ids

    def delete_multiple_cipher(self, cipher_ids: List[str], user_id_deleted: int) -> List[str]:
        current_time = now()
        # Update deleted_date of the ciphers
        ciphers_orm = self._get_multiple_ciphers_orm_by_user(
            user_id=user_id_deleted, only_deleted=True
        ).filter(
            id__in=cipher_ids, deleted_date__isnull=True
        ).exclude(type__in=IMMUTABLE_CIPHER_TYPES)
        deleted_cipher_ids = list(ciphers_orm.values_list('id', flat=True))
        for cipher_orm in ciphers_orm:
            cipher_orm.revision_date = current_time
            cipher_orm.deleted_date = current_time
        CipherORM.objects.bulk_update(ciphers_orm, ['revision_date', 'deleted_date'], batch_size=100)

        # Bump revision date: teams and user
        team_ids = ciphers_orm.exclude(team__isnull=True).values_list('team_id', flat=True)
        teams_orm = TeamORM.objects.filter(id__in=team_ids)
        for team_orm in teams_orm:
            bump_account_revision_date(team=team_orm)
        bump_account_revision_date(user=self._get_user_orm(user_id=user_id_deleted))
        return deleted_cipher_ids

    def restore_multiple_cipher(self, cipher_ids: List[str], user_id_restored: int) -> List[str]:
        current_time = now()
        user_restored_orm = self._get_user_orm(user_id=user_id_restored)
        ciphers_orm = self._get_multiple_ciphers_orm_by_user(
            user_id=user_id_restored, only_deleted=True
        ).filter(
            id__in=cipher_ids, deleted_date__isnull=False
        )
        # Restore all cipher by setting deleted_date as null
        restored_cipher_ids = list(ciphers_orm.values_list('id', flat=True))
        user_folder_ids = list(user_restored_orm.folders.values_list('id', flat=True))

        for cipher_orm in ciphers_orm:
            cipher_orm.revision_date = current_time
            cipher_orm.deleted_date = None
            folders = cipher_orm.get_folders()
            cipher_user_folder_id = folders.get(user_restored_orm.user_id)
            if cipher_user_folder_id and cipher_user_folder_id not in user_folder_ids:
                folders[user_restored_orm.user_id] = None
                cipher_orm.folders = folders
        CipherORM.objects.bulk_update(ciphers_orm, ['revision_date', 'deleted_date', 'folders'], batch_size=100)

        # Bump revision date: teams and user
        teams_orm = ciphers_orm.exclude(team__isnull=True).values_list('team', flat=True)
        for team_orm in teams_orm:
            bump_account_revision_date(team=team_orm)
        bump_account_revision_date(user=user_restored_orm)

        return restored_cipher_ids

    def delete_trash_ciphers(self, deleted_date_pivot: float) -> bool:
        CipherORM.objects.filter(
            deleted_date__isnull=False
        ).filter(deleted_date__lte=deleted_date_pivot).delete()
        return deleted_date_pivot
