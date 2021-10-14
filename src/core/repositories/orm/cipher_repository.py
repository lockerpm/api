from django.db.models import Q

from core.repositories import ICipherRepository
from core.utils.account_revision_date import bump_account_revision_date

from shared.utils.app import now
from shared.constants.members import *
from cystack_models.models.ciphers.ciphers import Cipher
from cystack_models.models.teams.teams import Team
from cystack_models.models.users.users import User
from cystack_models.models.teams.collections_members import CollectionMember
from cystack_models.models.teams.collections_groups import CollectionGroup


class CipherRepository(ICipherRepository):
    def get_favorite_users(self, cipher: Cipher):
        pass

    def get_folder_ids(self, cipher: Cipher):
        pass

    def get_by_id(self, cipher_id: str) -> Cipher:
        return Cipher.objects.get(id=cipher_id)

    def get_multiple_by_ids(self, cipher_ids: list):
        return Cipher.objects.filter(id__in=cipher_ids)

    def get_multiple_by_user(self, user: User, only_personal=False, only_managed_team=False, only_edited=False):
        """
        Get list ciphers of user
        :param user: (obj) User object
        :param only_personal: (bool) if True => Only get list personal ciphers
        :param only_managed_team: (bool) if True => Only get list ciphers of non-locked teams
        :param only_edited: (bool) if True => Only get list ciphers that user is allowed edit permisson
        :return:
        """

        personal_ciphers = Cipher.objects.filter(user=user)
        if only_personal is True:
            return personal_ciphers

        members = user.team_members.filter(status=PM_MEMBER_STATUS_CONFIRMED)
        if only_edited is True:
            members = members.filter(role__name__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN, MEMBER_ROLE_MANAGER])
        if only_managed_team:
            members = members.filter(team__locked=False)
        team_ids = list(members.values_list('team_id', flat=True))

        member_collections = CollectionMember.objects.filter(member__in=members).values_list('collection_id', flat=True)
        member_group_collections = CollectionGroup.objects.filter(
            group__groups_members__member__in=members
        ).values_list('collection_id', flat=True)
        team_collection_ids = list(member_collections) + list(member_group_collections)
        team_ciphers = Cipher.objects.filter(
            Q(collections_ciphers__collection_id__in=team_collection_ids) |
            Q(team_id__in=team_ids)
        )
        return (personal_ciphers | team_ciphers).distinct()

    def save_new_cipher(self, cipher_data):
        """
        Save new cipher
        :param cipher_data: (dict) Cipher data
        :return:
        """
        favorite = cipher_data.get("favorite", False)
        folder_id = cipher_data.get("folder_id", False)
        user_created_id = cipher_data.get("user_id")
        user_cipher_id = cipher_data.get("user_id")
        team_id = cipher_data.get("team_id")
        collection_ids = cipher_data.get("collection_ids", [])
        print("Collections", collection_ids)

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
            team_id=team_id
        )
        cipher.save()
        # Create CipherFavorite
        if user_created_id and favorite:
            cipher.set_favorite(user_cipher_id, True)
        # Create CipherFolder
        if folder_id:
            cipher.set_folder(user_cipher_id, folder_id)
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
            cipher.collections_ciphers.all().delete()
            cipher.collections_ciphers.model.create_multiple(cipher.id, *collection_ids)

        # Update revision date of user (if this cipher is personal)
        # or all related cipher members (if this cipher belongs to a team)
        bump_account_revision_date(team=cipher.team, **{
            "collection_ids": collection_ids,
            "role_name": [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]
        })
        bump_account_revision_date(user=cipher.user)

        return cipher

    def delete_multiple_cipher(self, cipher_ids: list, user_deleted: User = None):
        """
        Delete multiple ciphers by ids
        :param cipher_ids: (list) List cipher ids
        :param user_deleted: (obj) User deleted
        :return:
        """
        # Update deleted_date of the ciphers
        ciphers = Cipher.objects.filter(id__in=cipher_ids, deleted_date__isnull=True)
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
        ciphers = self.get_multiple_by_user(user=user_deleted, only_edited=True)
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
