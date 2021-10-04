from django.db.models import Q

from core.repositories import ICipherRepository

from shared.utils.app import now
from shared.constants.members import *
from cystack_models.models.ciphers.ciphers import Cipher
from cystack_models.models.teams.teams import Team
from cystack_models.models.users.users import User


class CipherRepository(ICipherRepository):
    def get_favorite_users(self, cipher: Cipher):
        pass

    def get_folder_ids(self, cipher: Cipher):
        pass

    def get_multiple_by_ids(self, cipher_ids: list):
        return Cipher.objects.filter(id__in=cipher_ids)

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
        cipher = Cipher.objects.filter(id__in=cipher_ids, deleted_date__isnull=True)
        team_ids = cipher.exclude(team__isnull=True).values_list('team_id', flat=True)
        cipher.update(revision_date=now(), deleted_date=now())
        # Bump revision date: teams and user
        if team_ids:
            teams = Team.objects.filter(id__in=team_ids)
            for team in teams:
                self._bump_account_revision_date(team=team)
        self._bump_account_revision_date(user=user_deleted)

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
