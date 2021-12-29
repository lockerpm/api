import uuid

from django.db.models import Q

from core.repositories import ISharingRepository
from core.utils.account_revision_date import bump_account_revision_date

from shared.constants.members import *
from shared.utils.app import now
from shared.utils.id_generator import sharing_id_generator
from cystack_models.models.ciphers.ciphers import Cipher
from cystack_models.models.ciphers.folders import Folder
from cystack_models.models.teams.teams import Team
from cystack_models.models.users.users import User
from cystack_models.models.members.team_members import TeamMember


class SharingRepository(ISharingRepository):
    def accept_invitation(self, member: TeamMember):
        """
        The user accepts the personal invitation
        :param member: (obj) Member object represents for the personal invitation
        :return:
        """
        # If member has a encrypted key => Set status CONFIRMED
        if member.key:
            member.status = PM_MEMBER_STATUS_CONFIRMED
        # Else, set status ACCEPTED
        else:
            member.status = PM_MEMBER_STATUS_ACCEPTED
        member.save()

    def reject_invitation(self, member: TeamMember):
        """
        This user rejects the personal invitation
        :param member:
        :return:
        """
        member.delete()

    def confirm_invitation(self, member: TeamMember, key: str):
        """
        The owner confirms the member of the personal sharing
        :param member: (obj)
        :param key: member org key
        :return:
        """
        member.email = None
        member.key = key
        member.status = PM_MEMBER_STATUS_CONFIRMED
        member.save()
        bump_account_revision_date(user=member.user)

    def create_new_sharing(self, sharing_key: str, members,
                           cipher: Cipher = None, folder: Folder = None, shared_collection_name: str = None):
        """
        Personal share a cipher or a folder
        :param sharing_key: (str) org key
        :param members: list shared members
        :param cipher: (obj) Cipher object
        :param folder: (obj) Folder object
        :param shared_collection_name: (str) Shared collection name
        :return:
        """
        user = folder.user if folder else cipher.user

        # Create new sharing id
        id_generator = sharing_id_generator(user_id=user.user_id)
        sharing_id = next(id_generator)

        from cystack_models.models.members.member_roles import MemberRole
        new_sharing = Team.create(**{
            "id": sharing_id,
            "name": "Sharing",
            "description": "",
            "personal_share": True,
            "members": [{
                "user": user,
                "role": MemberRole.objects.get(name=MEMBER_ROLE_OWNER),
                "is_default": False,
                "is_primary": True
            }]
        })
        new_sharing.key = sharing_key
        new_sharing.revision_date = now()

        # Save owner key for primary member
        primary_member = new_sharing.team_members.get(user=user)
        primary_member.key = sharing_key
        primary_member.external_id = uuid.uuid4()
        primary_member.save()

        # If user shares a folder => Create collection for this team
        shared_collection = None
        if shared_collection_name:
            shared_collection = new_sharing.collections.model.create(new_sharing, **{
                "name": shared_collection_name, "is_default": False
            })

        # Create sharing members
        non_existed_member_users = []
        existed_member_users = []
        for member in members:
            try:
                User.objects.get(user_id=member.get("user_id"))
                email = None
            except User.DoesNotExist:
                email = member.get("email")
            shared_member = new_sharing.team_members.model.objects.create(
                user_id=member.get("user_id"),
                email=email,
                role_id=member.get("role"),
                team=new_sharing,
                access_time=now(),
                is_primary=False,
                is_default=False,
                status=PM_MEMBER_STATUS_INVITED,
                key=member.get("key"),
            )

            # Create collection for this shared member
            if shared_member.role_id in [MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER] and shared_collection:
                shared_member.collections_members.model.objects.create(
                    collection=shared_collection, member=shared_member,
                    hide_passwords=member.get("hide_passwords", False)
                )
            if shared_member.role_id in [MEMBER_ROLE_MEMBER]:
                shared_member.hide_passwords = member.get("hide_password", False)
                shared_member.save()

            if shared_member.user_id:
                existed_member_users.append(shared_member.user_id)
            if shared_member.email:
                non_existed_member_users.append(shared_member.email)

        # Sharing this cipher or folder
        if folder and shared_collection:
            ciphers = user.ciphers.filter(
                Q(folders__icontains="{}: '{}'".format(user.user_id, folder.id)) |
                Q(folders__icontains='{}: "{}"'.format(user.user_id, folder.id))
            )
            ciphers.update(team=new_sharing, user=None, folders='')
            shared_cipher_ids = ciphers.values_list('id', flat=True)
            shared_collection.collections_ciphers.model.create_multiple_for_collection(
                shared_collection.id, *shared_cipher_ids
            )
            # Then, delete the root folder
            folder.delete()
        # Share a single cipher
        if cipher:
            cipher.user = None
            cipher.team = new_sharing
            cipher.save()

        return new_sharing, existed_member_users, non_existed_member_users
