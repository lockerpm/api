from django.db.models import Q

from core.repositories import ICipherRepository

from shared.utils.app import now
from shared.constants.members import *
from cystack_models.models.ciphers.ciphers import Cipher
from cystack_models.models.users.users import User


class CipherRepository(ICipherRepository):
    def get_favorite_users(self, cipher: Cipher):
        pass

    def get_folder_ids(self, cipher: Cipher):
        pass

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
        if team_id:
            # First, create collections for this cipher
            cipher.collections_ciphers.model.create_multiple(cipher.id, *collection_ids)
            # Finding all members collections
            member_user_ids = cipher.team.team_members.filter(status=PM_MEMBER_STATUS_CONFIRMED).filter(
                Q(role__name__in=[MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]) |
                Q(collections_members__collection_id__in=collection_ids)
            ).values_list('user_id', flat=True)
            # Update revision date of list members
            User.objects.filter(user_id__in=member_user_ids).update(revision_date=now())
        else:
            cipher.user.revision_date = now()
            cipher.user.save()

        return cipher

    def save_update_cipher(self, cipher_data):
        pass