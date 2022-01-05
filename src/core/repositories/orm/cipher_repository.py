import json
import uuid

from django.db.models import Q, Case, When, Value, IntegerField, BooleanField

from core.repositories import ICipherRepository
from core.utils.account_revision_date import bump_account_revision_date
from shared.constants.ciphers import *
from shared.utils.app import now, diff_list
from shared.constants.members import *
from cystack_models.models.ciphers.ciphers import Cipher
from cystack_models.models.teams.teams import Team
from cystack_models.models.users.users import User
from cystack_models.models.ciphers.folders import Folder
from cystack_models.models.teams.collections import Collection
from cystack_models.models.teams.collections_ciphers import CollectionCipher
from cystack_models.models.teams.collections_members import CollectionMember
from cystack_models.models.teams.collections_groups import CollectionGroup
from cystack_models.models.teams.groups_members import GroupMember


class CipherRepository(ICipherRepository):
    def get_by_id(self, cipher_id: str) -> Cipher:
        return Cipher.objects.get(id=cipher_id)

    def get_multiple_by_ids(self, cipher_ids: list):
        return Cipher.objects.filter(id__in=cipher_ids)

    def get_personal_ciphers(self, user):
        return Cipher.objects.filter(user=user)

    def get_team_ciphers(self, team):
        return Cipher.objects.filter(team=team)

    def get_multiple_by_user(self, user: User, only_personal=False, only_managed_team=False, only_edited=False,
                             exclude_team_ids=None, filter_ids=None):
        """
        Get list ciphers of user
        :param user: (obj) User object
        :param only_personal: (bool) if True => Only get list personal ciphers
        :param only_managed_team: (bool) if True => Only get list ciphers of non-locked teams
        :param only_edited: (bool) if True => Only get list ciphers that user is allowed edit permission
        :param exclude_team_ids: (list) Excluding all ciphers have team_id in this list
        :param filter_ids: (list) List filtered cipher ids
        :return:
        """

        personal_ciphers = self.get_personal_ciphers(user=user)
        if filter_ids:
            personal_ciphers = personal_ciphers.filter(id__in=filter_ids)
        if only_personal is True:
            return personal_ciphers.annotate(view_password=Value(True, output_field=BooleanField()))

        confirmed_team_members = user.team_members.filter(status=PM_MEMBER_STATUS_CONFIRMED)
        if only_managed_team:
            confirmed_team_members = confirmed_team_members.filter(team__locked=False)

        if exclude_team_ids:
            confirmed_team_members = confirmed_team_members.exclude(team_id__in=exclude_team_ids)

        confirmed_team_ids = confirmed_team_members.values_list('team_id', flat=True)
        team_ciphers = Cipher.objects.filter(
            team_id__in=confirmed_team_ids
        )
        if filter_ids:
            team_ciphers = team_ciphers.filter(id__in=filter_ids)

        team_ciphers = team_ciphers.filter(
            # Owner, Admin ciphers
            Q(
                team__team_members__role_id__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN],
                team__team_members__user=user
            ) |
            # Group access all ciphers
            Q(
                team__groups__access_all=True,
                team__groups__groups_members__member__user=user
            ) |
            # Team member
            Q(
                collections_ciphers__collection__collections_members__member__in=confirmed_team_members,
                team__team_members__user=user
            ) |
            Q(
                collections_ciphers__collection__collections_groups__group__groups_members__member__in=confirmed_team_members,
                team__team_members__user=user
            ) |
            # Personal share
            Q(
                team__personal_share=True,
                team__team_members__user=user
            )
        ).distinct().annotate(
            view_password=Case(
                When(
                    Q(
                        team__team_members__role_id__in=[MEMBER_ROLE_MEMBER],
                        team__team_members__user=user,
                        collections_ciphers__collection__collections_members__hide_passwords=True
                    ), then=False
                ),
                When(
                    Q(
                        team__team_members__role_id__in=[MEMBER_ROLE_MEMBER],
                        team__team_members__user=user,
                        team__personal_share=True,
                        team__team_members__hide_passwords=True
                    ), then=False
                ),
                default=True,
                output_field=BooleanField()
            )
        )
        hide_password_cipher_ids = team_ciphers.filter(view_password=False).values_list('id', flat=True)
        if only_edited:
            team_ciphers = team_ciphers.filter(
                team__team_members__role_id__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER],
                team__team_members__user=user
            )
        return Cipher.objects.filter(
            id__in=list(personal_ciphers.values_list('id', flat=True)) + list(team_ciphers.values_list('id', flat=True))
        ).annotate(
            view_password=Case(
                When(id__in=hide_password_cipher_ids, then=False),
                default=True,
                output_field=BooleanField()
            )
        )

    def save_new_cipher(self, cipher_data):
        """
        Save new cipher
        :param cipher_data: (dict) Cipher data
        :return:
        """
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
        cipher = Cipher(
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
        cipher.save()
        # Create CipherFavorite
        if user_created_id and favorite:
            cipher.set_favorite(user_created_id, True)
        # Create CipherFolder
        if user_created_id and folder_id:
            cipher.set_folder(user_created_id, folder_id)
        # Create CipherCollections
        if team_id:
            cipher.collections_ciphers.model.create_multiple(cipher.id, *collection_ids)

        # Update revision date of user (if this cipher is personal)
        # or all related cipher members (if this cipher belongs to a team)
        bump_account_revision_date(team=cipher.team, **{
            "collection_ids": collection_ids,
            "role_name": [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]
        })
        bump_account_revision_date(user=cipher.user)
        return cipher

    def save_update_cipher(self, cipher: Cipher, cipher_data):
        user_created_id = cipher_data.get("user_id")
        user_cipher_id = cipher_data.get("user_id")
        team_id = cipher_data.get("team_id")
        collection_ids = cipher_data.get("collection_ids", [])

        # If team_id is not null => This cipher belongs to team
        if team_id:
            user_cipher_id = None
        # Create new cipher object
        cipher.revision_date = now()
        cipher.reprompt = cipher_data.get("reprompt", cipher.reprompt) or 0
        cipher.score = cipher_data.get("score", cipher.score)
        cipher.type = cipher_data.get("type", cipher.type)
        cipher.data = cipher_data.get("data", cipher.get_data())
        cipher.user_id = user_cipher_id
        cipher.team_id = team_id
        cipher.save()
        # Set favorite
        if user_created_id:
            favorite = cipher_data.get("favorite", cipher.get_favorites().get(user_cipher_id, False))
            cipher.set_favorite(user_id=user_cipher_id, is_favorite=favorite)

        # Set folder id
        folder_id = cipher_data.get("folder_id", cipher.get_folders().get(user_cipher_id))
        cipher.set_folder(user_cipher_id, folder_id)
        # Create CipherCollections
        if team_id:
            existed_collection_ids = list(cipher.collections_ciphers.values_list('collection_id', flat=True))
            removed_collection_ids = diff_list(existed_collection_ids, collection_ids)
            added_collection_ids = diff_list(collection_ids, existed_collection_ids)
            cipher.collections_ciphers.filter(collection_id__in=removed_collection_ids).delete()
            cipher.collections_ciphers.model.create_multiple(cipher.id, *added_collection_ids)

        # Update revision date of user (if this cipher is personal)
        # or all related cipher members (if this cipher belongs to a team)
        bump_account_revision_date(team=cipher.team, **{
            "collection_ids": collection_ids,
            "role_name": [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]
        })
        bump_account_revision_date(user=cipher.user)

        return cipher

    def save_share_cipher(self, cipher: Cipher, cipher_data) -> Cipher:
        return self.save_update_cipher(cipher, cipher_data)

    def delete_multiple_cipher(self, cipher_ids: list, user_deleted: User = None):
        """
        Delete multiple ciphers by ids
        :param cipher_ids: (list) List cipher ids
        :param user_deleted: (obj) User deleted
        :return:
        """
        # Update deleted_date of the ciphers
        # ciphers = Cipher.objects.filter(id__in=cipher_ids, deleted_date__isnull=True)
        ciphers = self.get_multiple_by_user(user=user_deleted, only_edited=True).filter(
            id__in=cipher_ids, deleted_date__isnull=True
        )
        team_ids = ciphers.exclude(team__isnull=True).values_list('team_id', flat=True)
        ciphers.update(revision_date=now(), deleted_date=now())
        # Bump revision date: teams and user
        teams = Team.objects.filter(id__in=team_ids)
        for team in teams:
            bump_account_revision_date(team=team)
        bump_account_revision_date(user=user_deleted)

    def delete_permanent_multiple_cipher(self, cipher_ids: list, user_deleted: User):
        """
        Delete permanently ciphers by ids
        :param cipher_ids: (list) List cipher ids
        :param user_deleted: (obj) User deleted
        :return:
        """
        ciphers = self.get_multiple_by_user(user=user_deleted, only_edited=True).filter(id__in=cipher_ids)
        team_ids = ciphers.exclude(team__isnull=True).values_list('team_id', flat=True)
        # Delete ciphers objects
        ciphers.delete()
        # Bump revision date: teams and user
        teams = Team.objects.filter(id__in=team_ids)
        for team in teams:
            bump_account_revision_date(team=team)
        bump_account_revision_date(user=user_deleted)

    def restore_multiple_cipher(self, cipher_ids: list, user_restored: User):
        """
        Restore ciphers by ids
        :param cipher_ids: (list) List cipher ids
        :param user_restored: (obj) User object
        :return:
        """
        # Filter list ciphers from trash
        ciphers = self.get_multiple_by_user(user=user_restored, only_edited=True).filter(
            id__in=cipher_ids, deleted_date__isnull=False
        )
        # Restore all cipher by setting deleted_date as null
        ciphers.update(revision_date=now(), deleted_date=None)
        # Bump revision date: teams and user
        teams = ciphers.exclude(team__isnull=True).values_list('team', flat=True)
        for team in teams:
            bump_account_revision_date(team=team)
        bump_account_revision_date(user=user_restored)

    def move_multiple_cipher(self, cipher_ids, user_moved, folder_id):
        # Filter list ciphers of users
        ciphers = self.get_multiple_by_user(user=user_moved).filter(id__in=cipher_ids, deleted_date__isnull=True)
        # Move all cipher to new folder
        for cipher in ciphers:
            cipher.set_folder(user_id=user_moved.user_id, folder_id=folder_id)
        # Bump revision date of user
        bump_account_revision_date(user=user_moved)

    def import_multiple_cipher(self, user: User, ciphers, folders, folder_relationships):
        # Init id for folders
        existed_folder_ids = list(Folder.objects.filter(user=user).values_list('id', flat=True))
        for folder in folders:
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

            cipher["folders"] = "{%d: '%s'}" % (user.user_id, folder.get("id"))

        # Create multiple folders
        import_folders = []
        for folder in folders:
            import_folders.append(
                Folder(id=folder["id"], name=folder["name"], user=user, creation_date=now(), revision_date=now())
            )
        Folder.objects.bulk_create(import_folders, batch_size=100, ignore_conflicts=True)

        # Create multiple ciphers
        import_ciphers = []
        for cipher_data in ciphers:
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
            import_ciphers.append(
                Cipher(
                    creation_date=cipher_data.get("creation_date", now()),
                    revision_date=cipher_data.get("revision_date", now()),
                    deleted_date=cipher_data.get("deleted_date"),
                    reprompt=cipher_data.get("reprompt", 0) or 0,
                    score=cipher_data.get("score", 0),
                    type=cipher_data.get("type"),
                    data=cipher_data.get("data"),
                    user_id=user.user_id,
                    folders=cipher_data.get("folders", ""),
                    team_id=cipher_data.get("organizationId")
                )
            )
        Cipher.objects.bulk_create(import_ciphers, batch_size=100, ignore_conflicts=True)
        bump_account_revision_date(user=user)

    def sync_personal_cipher_offline(self, user: User, ciphers, folders, folder_relationships):
        # Init id for folders
        existed_folder_ids = list(Folder.objects.filter(user=user).values_list('id', flat=True))
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

            cipher["folders"] = "{%d: '%s'}" % (user.user_id, folder.get("id"))

        # Create multiple folders
        sync_folders = []
        for folder in folders:
            sync_folders.append(
                Folder(id=folder["id"], name=folder["name"], user=user, creation_date=now(), revision_date=now())
            )
        Folder.objects.bulk_create(sync_folders, batch_size=100, ignore_conflicts=True)

        # Create multiple ciphers
        sync_create_ciphers = []
        sync_create_ciphers_data = [cipher_data for cipher_data in ciphers if not cipher_data.get("id")]
        for cipher_data in sync_create_ciphers_data:
            # Only allow sync personal ciphers
            if cipher_data.get("organizationId") or cipher_data.get("team"):
                continue
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

            sync_create_ciphers.append(
                Cipher(
                    creation_date=cipher_data.get("creationDate", now()),
                    revision_date=cipher_data.get("revisionDate", now()),
                    deleted_date=cipher_data.get("deletedDate"),
                    reprompt=cipher_data.get("reprompt", 0) or 0,
                    score=cipher_data.get("score", 0),
                    type=cipher_data.get("type"),
                    data=cipher_data.get("data"),
                    user_id=user.user_id,
                    folders=cipher_data.get("folders", ""),
                    team_id=cipher_data.get("organizationId")
                )
            )

        Cipher.objects.bulk_create(sync_create_ciphers, batch_size=100, ignore_conflicts=True)

        # Sync update existed ciphers
        sync_update_ciphers = []
        sync_update_ciphers_data = [cipher_data for cipher_data in ciphers if cipher_data.get("id")]
        sync_update_cipher_ids = [cipher_data.get("id") for cipher_data in sync_update_ciphers_data]
        user_update_ciphers = user.ciphers.filter(id__in=sync_update_cipher_ids)
        user_update_ciphers_dict = {}
        for cipher in user_update_ciphers:
            user_update_ciphers_dict[cipher.id] = cipher
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
            cipher_obj.user_id = user.user_id
            cipher_obj.folders = cipher_data.get("folders", "")
            cipher_obj.team_id = cipher_data.get("organizationId")
            sync_update_ciphers.append(cipher_obj)

        Cipher.objects.bulk_update(
            sync_update_ciphers,
            ['creation_date', 'revision_date', 'deleted_date', 'reprompt', 'score', 'type',
             'data', 'user_id', 'folders', 'team_id'],
            batch_size=100
        )
        bump_account_revision_date(user=user)

    def import_multiple_cipher_team(self, team: Team, ciphers, collections, collection_relationships):
        # Init id for collections
        existed_collection_ids = list(team.collections.values_list('id', flat=True))
        for collection in collections:
            while True:
                new_collection_id = str(uuid.uuid4())
                if new_collection_id not in existed_collection_ids:
                    break
            collection["id"] = new_collection_id

        # Init id for ciphers
        existed_cipher_ids = list(team.ciphers.values_list('id', flat=True))
        for cipher in ciphers:
            while True:
                new_cipher_id = str(uuid.uuid4())
                if new_cipher_id not in existed_cipher_ids:
                    break
            cipher["id"] = new_cipher_id

        # Create the collection associations based on the newly created collection ids
        collection_ciphers = []
        for collection_relationship in collection_relationships:
            try:
                cipher = ciphers[collection_relationship["key"]]
                collection = collections[collection_relationship["value"]]
            except (KeyError, ValueError):
                continue
            collection_ciphers.append({"cipher_id": cipher.get("id"), "collection_id": collection.get("id")})

        # Create multiple collections
        import_collections = []
        for collection in collections:
            import_collections.append(
                Collection(
                    id=collection.get("id"), team=team, name=collection.get("name"),
                    creation_date=now(return_float=True), revision_date=now(return_float=True),
                    external_id=None, is_default=False
                )
            )
        Collection.objects.bulk_create(import_collections, batch_size=100, ignore_conflicts=True)

        # Create multiple ciphers
        import_ciphers = []
        for cipher_data in ciphers:
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
            cipher_data.pop("team", None)
            cipher_data = json.loads(json.dumps(cipher_data))
            import_ciphers.append(
                Cipher(
                    id=cipher_data.get("id"),
                    creation_date=cipher_data.get("creation_date", now()),
                    revision_date=cipher_data.get("revision_date", now()),
                    deleted_date=cipher_data.get("deleted_date"),
                    reprompt=cipher_data.get("reprompt", 0) or 0,
                    score=cipher_data.get("score", 0),
                    type=cipher_data.get("type"),
                    data=cipher_data.get("data"),
                    team_id=team.id,
                    folders=cipher_data.get("folders", ""),
                )
            )
        Cipher.objects.bulk_create(import_ciphers, batch_size=100, ignore_conflicts=True)

        # Create collection cipher
        import_collection_ciphers = []
        for collection_cipher in collection_ciphers:
            import_collection_ciphers.append(
                CollectionCipher(
                    cipher_id=collection_cipher.get("cipher_id"),
                    collection_id=collection_cipher.get("collection_id")
                )
            )
        CollectionCipher.objects.bulk_create(import_collection_ciphers, batch_size=100, ignore_conflicts=True)
        # Bump account revision date
        bump_account_revision_date(team=team)
