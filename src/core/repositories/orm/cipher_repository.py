from django.db.models import Q

from core.repositories import ICipherRepository

from shared.utils.app import now
from shared.constants.members import *
from cystack_models.models.ciphers.ciphers import Cipher
from cystack_models.models.ciphers.ciphers_folders import CipherFolder
from cystack_models.models.teams.teams import Team
from cystack_models.models.users.users import User
from cystack_models.models.teams.collections_members import CollectionMember
from cystack_models.models.teams.collections_groups import CollectionGroup


class CipherRepository(ICipherRepository):
    def get_favorite_users(self, cipher: Cipher):
        pass

    def get_folder_ids(self, cipher: Cipher):
        pass

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
            members = members.filter(role__name__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN])
        if only_managed_team:
            members = members.filter(team__locked=False)

        member_collections = CollectionMember.objects.filter(member__in=members).values_list('collection_id', flat=True)
        member_group_collections = CollectionGroup.objects.filter(
            group__groups_members__in=members
        ).values_list('collection_id', flat=True)
        team_collection_ids = list(member_collections) + list(member_group_collections)
        team_ciphers = Cipher.objects.filter(
            collections_ciphers__collection_id__in=team_collection_ids
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

        # If team_id is not null => This cipher belongs to team
        if team_id:
            user_cipher_id = None
        # Create new cipher object
        cipher = Cipher(
            creation_date=cipher_data.get("creation_date", now()),
            revision_date=cipher_data.get("revision_date", now()),
            deleted_date=cipher_data.get("deleted_date"),
            reprompt=cipher_data.get("reprompt", 0),
            score=cipher_data.get("score", 0),
            type=cipher_data.get("type"),
            data=cipher_data.get("data"),
            user_id=user_cipher_id,
            team_id=team_id
        )
        cipher.save()
        # Create CipherFavorite
        if user_created_id and favorite:
            cipher.ciphers_favorites.model.retrieve_or_create(cipher.id, user_created_id)
        # Create CipherFolder
        if folder_id:
            cipher.ciphers_folders.model.retrieve_or_create(cipher.id, folder_id)

        # Update revision date of user (if this cipher is personal)
        # or all related cipher members (if this cipher belongs to a team)
        self._bump_account_revision_date(user=cipher.user, team=cipher.team, **{
            "collection_ids": collection_ids,
            "role_name": [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]
        })

        return cipher

    def save_update_cipher(self, cipher_data):
        pass

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
            self._bump_account_revision_date(team=team)
        self._bump_account_revision_date(user=user_deleted)

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
            self._bump_account_revision_date(team=team)
        self._bump_account_revision_date(user=user_deleted)

    def restore_multiple_cipher(self, cipher_ids: list, user_restored: User):
        """
        Restore ciphers by ids
        :param cipher_ids: (list) List cipher ids
        :param user_restored: (obj) User object
        :return:
        """
        # Filter list ciphers from trash
        ciphers = self.get_multiple_by_user(user=user_restored, only_edited=True).filter(
            deleted_date__isnull=False
        )
        # Restore all cipher by setting deleted_date as null
        ciphers.update(revision_date=now(), deleted_date=None)
        # Bump revision date: teams and user
        teams = ciphers.exclude(team__isnull=True).values_list('team', flat=True)
        for team in teams:
            self._bump_account_revision_date(team=team)
        self._bump_account_revision_date(user=user_restored)

    def move_multiple_cipher(self, cipher_ids, user_moved, folder_id):
        # Filter list ciphers of users
        ciphers = self.get_multiple_by_user(user=user_moved).filter(deleted_date__isnull=True)
        # Move all cipher to new folder
        # First, delete old cipher folder
        CipherFolder.objects.filter(cipher__in=ciphers, folder__user=user_moved).delete()
        # Create new cipher folder
        if folder_id:
            CipherFolder.create_multiple(folder_id=folder_id, *ciphers)
        # Bump revision date of user
        self._bump_account_revision_date(user=user_moved)

    def _bump_account_revision_date(self, user: User = None, team=None, **team_filters):
        if team:
            # Finding all members
            team_members = team.team_members.filter(status=PM_MEMBER_STATUS_CONFIRMED)
            collection_ids = team_filters.get("collection_ids", [])
            role_name = team_filters.get("role_name", [])
            # Filter by collection ids
            if collection_ids:
                team_members = team_members.filter(
                    Q(role_name__in=role_name) | Q(collections_members__collection_id__in=collection_ids)
                )

            # Get list user ids and update revision date of them
            member_user_ids = team_members.values_list('user_id', flat=True)
            User.objects.filter(user_id__in=member_user_ids).update(revision_date=now())
        elif user:
            user.revision_date = now()
            user.save()
