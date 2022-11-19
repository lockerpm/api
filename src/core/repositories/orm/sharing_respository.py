import uuid

from django.db.models import When, Q, Value, Case, IntegerField, Count

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
from cystack_models.models.teams.groups import Group
from cystack_models.models.teams.groups_members import GroupMember
from cystack_models.models.enterprises.groups.groups import EnterpriseGroup


class SharingRepository(ISharingRepository):
    def get_personal_share_type(self, member: TeamMember):
        role = member.role_id
        if role in [MEMBER_ROLE_MEMBER]:
            if member.hide_passwords is True:
                return MEMBER_SHARE_TYPE_ONLY_FILL
            else:
                return MEMBER_SHARE_TYPE_VIEW
        return MEMBER_SHARE_TYPE_EDIT

    def get_share_type(self, role_id: str):
        return MEMBER_SHARE_TYPE_VIEW if role_id in [MEMBER_ROLE_MEMBER] else MEMBER_SHARE_TYPE_EDIT

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
        bump_account_revision_date(user=member.user)
        return member

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

    def update_role_invitation(self, member: TeamMember, role_id: str, hide_passwords: bool = None):
        """
        The owner updates the role of the member personal sharing
        :param member: (obj) Member obj
        :param role_id: (str) The role id
        :param hide_passwords: (bool)
        :return:
        """
        member.role_id = role_id
        if role_id in [MEMBER_ROLE_MEMBER]:
            member.hide_passwords = hide_passwords
        member.save()
        # Bump revision date
        bump_account_revision_date(user=member.user)
        return member

    def update_group_role_invitation(self, group: Group, role_id: str):
        """
        The owner updates the role of the group personal sharing
        :param group:
        :param role_id:
        :return:
        """
        group.role_id = role_id
        group.save()
        group_user_ids = group.groups_members.values_list('member__user_id', flat=True)
        group.team.team_members.filter(is_added_by_group=True, user_id__in=group_user_ids).update(role_id=role_id)
        # Bump revision date
        bump_account_revision_date(team=group.team, **{"group_ids": [group.enterprise_group_id]})
        return group

    def stop_share_all_members(self, team, cipher=None, cipher_data=None,
                               collection=None, personal_folder_name: str = None, personal_folder_ciphers=None):

        # Get owner
        user_owner = team.team_members.get(role_id=MEMBER_ROLE_OWNER, is_primary=True).user
        other_members = list(team.team_members.exclude(user=user_owner).values_list('user_id', flat=True))

        # If the team shared a folder
        if collection:
            # Create personal folder of the owner
            personal_folder = Folder(
                name=personal_folder_name, user=user_owner, creation_date=now(), revision_date=now()
            )
            personal_folder.save()
            # Get all ciphers of the shared team
            shared_folder_cipher_ids = [cipher["id"] for cipher in personal_folder_ciphers]
            ciphers = team.ciphers.filter(id__in=shared_folder_cipher_ids)

            # Update new cipher data
            for c in ciphers:
                personal_cipher_data = next(
                    (item for item in personal_folder_ciphers if item["id"] == c.id), {}
                )
                self._stop_share_cipher(cipher=c, user_id=user_owner.user_id, cipher_data=personal_cipher_data)

            # Update folder
            Cipher.objects.filter(id__in=shared_folder_cipher_ids).update(
                folders=str({user_owner.user_id: str(personal_folder.id)})
            )

        # If the team shared a cipher
        if cipher:
            self._stop_share_cipher(cipher=cipher, user_id=user_owner.user_id, cipher_data=cipher_data)

        # Delete this team
        team.ciphers.all().delete()
        team.collections.all().delete()
        team.groups.all().delete()
        team.delete()

        # Update revision date of user
        bump_account_revision_date(user=user_owner)
        return other_members

    def stop_share(self, member: TeamMember = None, group: Group = None,
                   cipher=None, cipher_data=None,
                   collection=None, personal_folder_name: str = None, personal_folder_ciphers=None):
        """
        The owner stops share a item (or a collection) with a member
        :param member: (object) TeamMember object will be removed
        :param group: (object) The Group object will be removed
        :param cipher: (obj) Cipher object
        :param cipher_data: (obj) New cipher data if the cipher does not share with any members
        :param collection: (obj) Team collection will be stopped sharing
        :param personal_folder_name: (obj) New folder name if the collection does not share with any members
        :param personal_folder_ciphers: (obj) List new ciphers data in the collection if the user stops sharing
        :return: The member user id has been removed
        """
        team = group.team if group else member.team

        # Get owner
        user_owner = team.team_members.get(role_id=MEMBER_ROLE_OWNER, is_primary=True).user

        # Remove this member / group from the team
        if group:
            group_members_user_ids = group.groups_members.values('member__user_id', flat=True)
            deleted_members = team.team_members.annotate(
                group_count=Count('groups_members')
            ).filter(user_id__in=group_members_user_ids, is_added_by_group=True, group_count=1)
            deleted_members_user_ids = deleted_members.values_list('user_id', flat=True)
            deleted_members.delete()
            group.delete()
        if member:
            deleted_members_user_ids = [member.user_id]
            member.delete()

        # If the team does not have any members (excluding owner)
        # => Remove shared team and change the cipher/collection to personal cipher/personal folder
        if team.team_members.exclude(role_id=MEMBER_ROLE_OWNER).exists() is False:
            self.stop_share_all_members(team=team, cipher=cipher, cipher_data=cipher_data,
                                        collection=collection, personal_folder_name=personal_folder_name,
                                        personal_folder_ciphers=personal_folder_ciphers)

        # Update revision date of user
        if group:
            bump_account_revision_date(team=team, **{"group_ids": [group.enterprise_group_id]})
        else:
            bump_account_revision_date(user=member.user)
        bump_account_revision_date(user=user_owner)

        return deleted_members_user_ids

    def delete_share_folder(self, team, collection=None, personal_folder_name: str = None, personal_folder_ciphers=None):
        # Get owner
        user_owner = team.team_members.get(role_id=MEMBER_ROLE_OWNER, is_primary=True).user
        other_members = list(team.team_members.exclude(user=user_owner).values_list('user_id', flat=True))

        # Get all ciphers of the shared team
        shared_folder_cipher_ids = [cipher["id"] for cipher in personal_folder_ciphers]
        ciphers = team.ciphers.filter(id__in=shared_folder_cipher_ids)

        # Update new cipher data
        for c in ciphers:
            personal_cipher_data = next(
                (item for item in personal_folder_ciphers if item["id"] == c.id), {}
            )
            self._stop_share_cipher(cipher=c, user_id=user_owner.user_id, cipher_data=personal_cipher_data)

        # Move ciphers to the trash
        Cipher.objects.filter(id__in=shared_folder_cipher_ids).update(revision_date=now(), deleted_date=now())

        # Delete this team
        team.ciphers.all().delete()
        team.collections.all().delete()
        team.groups.all().delete()
        team.delete()

        # Update revision date of user
        bump_account_revision_date(user=user_owner)
        return other_members

    def leave_share(self, member: TeamMember):
        """
        The member leaves the sharing team
        :param member: (obj) The member obj
        :return:
        """
        bump_account_revision_date(user=member.user)
        member_user_id = member.user_id
        member.delete()
        return member_user_id

    def create_new_sharing(self, sharing_key: str, members, groups=None,
                           cipher: Cipher = None, shared_cipher_data=None,
                           folder: Folder = None, shared_collection_name: str = None, shared_collection_ciphers=None):
        """
        Personal share a cipher or a folder
        :param sharing_key: (str) org key
        :param members: list shared members
        :param groups: list shared groups
        :param cipher: (obj) Cipher object
        :param shared_cipher_data: (dict) New shared cipher data
        :param folder: (obj) Folder object
        :param shared_collection_name: (str) Shared collection name
        :param shared_collection_ciphers: (list) List shared ciphers
        :return:
        """
        if folder:
            user = folder.user
        else:
            if cipher.team:
                user = cipher.team.team_members.get(role_id=MEMBER_ROLE_OWNER, is_primary=True).user
            else:
                user = cipher.user

        # If the cipher is shared => The sharing team is the team of the cipher
        if cipher and cipher.team:
            new_sharing = cipher.team
        # Else, create new sharing team
        else:
            from cystack_models.models.members.member_roles import MemberRole
            # Create new sharing id
            id_generator = sharing_id_generator(user_id=user.user_id)
            sharing_id = next(id_generator)
            team_name = user.get_from_cystack_id().get("full_name", "Sharing")
            new_sharing = Team.create(**{
                "id": sharing_id,
                "name": team_name,
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
            new_sharing.save()

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
        existed_member_users, non_existed_member_users = self.add_members(
            team=new_sharing, shared_collection=shared_collection, members=members, groups=groups
        )

        # Sharing the folder
        if folder and shared_collection:
            shared_collection_cipher_ids = [collection_cipher["id"] for collection_cipher in shared_collection_ciphers]
            ciphers = user.ciphers.filter(id__in=shared_collection_cipher_ids)
            shared_cipher_ids = []
            # Update new cipher data
            for cipher in ciphers:
                shared_cipher_data = next(
                    (item for item in shared_collection_ciphers if item["id"] == cipher.id), {}
                )
                shared_cipher_ids.append(cipher.id)
                self._share_cipher(cipher=cipher, team_id=new_sharing.id, cipher_data=shared_cipher_data)

            # Delete all folders of the ciphers
            Cipher.objects.filter(id__in=shared_cipher_ids).update(folders="")
            # Create a collection for the shared ciphers
            shared_collection.collections_ciphers.model.create_multiple_for_collection(
                shared_collection.id, *shared_cipher_ids
            )
            # Then, delete the root folder
            folder.delete()

        # Share a single cipher
        if cipher:
            if not cipher.team:
                self._share_cipher(cipher=cipher, team_id=new_sharing.id, cipher_data=shared_cipher_data)

        # Update revision date of the user
        bump_account_revision_date(team=new_sharing)

        return new_sharing, existed_member_users, non_existed_member_users

    def _share_cipher(self, cipher: Cipher, team_id, cipher_data):
        # Update the cipher object
        cipher.revision_date = now()
        cipher.reprompt = cipher_data.get("reprompt", cipher.reprompt) or 0
        cipher.score = cipher_data.get("score", cipher.score)
        cipher.type = cipher_data.get("type", cipher.type)
        cipher.data = cipher_data.get("data", cipher.get_data())
        cipher.user_id = None
        cipher.team_id = team_id
        cipher.save()
        return cipher

    def _stop_share_cipher(self, cipher: Cipher, user_id, cipher_data):
        # Change team cipher to user cipher
        cipher.revision_date = now()
        cipher.reprompt = cipher_data.get("reprompt", cipher.reprompt) or 0
        cipher.score = cipher_data.get("score", cipher.score)
        cipher.type = cipher_data.get("type", cipher.type)
        cipher.data = cipher_data.get("data", cipher.get_data())
        cipher.user_id = user_id
        cipher.team_id = None
        cipher.save()
        return cipher

    def add_members(self, team, shared_collection, members, groups=None):
        non_existed_member_users = []
        existed_member_users = []
        existed_user_ids = list(team.team_members.filter(user_id__isnull=False).values_list('user_id', flat=True))
        existed_emails = list(team.team_members.filter(email__isnull=False).values_list('email', flat=True))
        for member in members:
            try:
                member_user = User.objects.get(user_id=member.get("user_id"), activated=True)
                email = None
            except User.DoesNotExist:
                member_user = None
                email = member.get("email")
            if member_user and member_user.user_id in existed_user_ids:
                continue
            if email and email in existed_emails:
                continue
            member_data = {"user": member_user, "email": email, "role": member.get("role"), "key": member.get("key")}
            shared_member = self.__create_shared_member(
                team=team, member_data=member_data, shared_collection=shared_collection
            )
            if shared_member.user_id:
                existed_member_users.append(shared_member.user_id)
                existed_user_ids.append(shared_member.user_id)
            if shared_member.email:
                non_existed_member_users.append(shared_member.email)
                existed_emails.append(shared_member.email)

        if groups:
            existed_group_member_users, non_existed_group_member_users = self.add_group_members(
                team=team, shared_collection=shared_collection, groups=groups
            )
            existed_member_users += existed_group_member_users
            non_existed_member_users += non_existed_group_member_users
        return list(set(existed_member_users)), list(set(non_existed_member_users))

    @staticmethod
    def __create_shared_member(team, member_data, shared_collection=None):
        # shared_member = team.team_members.model.objects.create(
        #     user=member.get("user"),
        #     email=member.get("email"),
        #     role_id=member.get("role"),
        #     key=member.get("key"),
        #     team=team,
        #     access_time=now(),
        #     is_primary=False,
        #     is_default=False,
        #     status=PM_MEMBER_STATUS_INVITED,
        # )

        shared_member = team.team_members.model.create_with_data(team, role_id=member_data.get("role"), **{
            "user": member_data.get("user"),
            "email": member_data.get("email"),
            "key": member_data.get("key"),
            "is_added_by_group": member_data.get("is_added_by_group", False),
            "status": PM_MEMBER_STATUS_INVITED,
            "group_id": member_data.get("group_id")
        })

        # Create collection for this shared member
        if shared_member.role_id in [MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER] and shared_collection:
            shared_member.collections_members.model.objects.create(
                collection=shared_collection, member=shared_member,
                hide_passwords=member_data.get("hide_passwords", False)
            )
        # DEPRECATED: Not use hide_passwords
        # if shared_member.role_id in [MEMBER_ROLE_MEMBER]:
        #     shared_member.hide_passwords = member.get("hide_passwords", False)
        #     shared_member.save()
        return shared_member

    def add_group_members(self, team, shared_collection, groups):
        non_existed_member_users = []
        existed_member_users = []
        existed_user_ids = list(team.team_members.filter(user_id__isnull=False).values_list('user_id', flat=True))
        existed_emails = list(team.team_members.filter(email__isnull=False).values_list('email', flat=True))

        members_groups_data = [group.get("members") or [] for group in groups]
        members_groups_user_ids = []
        for members_group_data in members_groups_data:
            members_groups_user_ids += [m.get("user_id") for m in members_group_data if m.get("user_id")]
        members_groups_users = User.objects.filter(user_id__in=members_groups_user_ids, activated=True)
        members_groups_users_dict = dict()
        for u in members_groups_users:
            members_groups_users_dict[u.user_id] = u

        for group in groups:
            members = group.get("members") or []
            team_group = team.groups.model.retrieve_or_create(
                team.id, group.get("id"), **{
                    "role_id": group.get("role") or group.get("role_id") or MEMBER_ROLE_MEMBER
                }
            )
            for member in members:
                member_user = members_groups_users_dict.get(member.get("user_id"))
                email = None if member_user else member.get("email")

                if member_user and member_user.user_id in existed_user_ids:
                    continue
                if email and email in existed_emails:
                    continue
                member_data = {
                    "user": member_user,
                    "email": email,
                    "role": member.get("role"),
                    "key": member.get("key"),
                    "is_added_by_group": True,
                    "group_id": team_group.id,
                }
                shared_member = self.__create_shared_member(
                    team=team, member_data=member_data, shared_collection=shared_collection
                )
                if shared_member.user_id:
                    existed_member_users.append(shared_member.user_id)
                    existed_user_ids.append(shared_member.user_id)
                if shared_member.email:
                    non_existed_member_users.append(shared_member.email)
                    existed_emails.append(shared_member.email)
        return existed_member_users, non_existed_member_users

    def get_my_personal_shared_teams(self, user: User):
        """
        Get list personal shared team that user is owner
        :param user:
        :return:
        """
        teams = Team.objects.filter(
            team_members__user=user,
            team_members__role_id=MEMBER_ROLE_OWNER,
            team_members__status=PM_MEMBER_STATUS_CONFIRMED,
            key__isnull=False,
            personal_share=True
        )
        return teams

    def get_shared_members(self, personal_shared_team: Team, exclude_owner=True, is_added_by_group=None):
        """
        Get list member of personal shared team
        :param personal_shared_team:
        :param exclude_owner:
        :param is_added_by_group:
        :return:
        """
        order_whens = [
            When(Q(role__name=MEMBER_ROLE_OWNER, user__isnull=False), then=Value(2)),
            When(Q(role__name=MEMBER_ROLE_ADMIN, user__isnull=False), then=Value(3)),
            When(Q(role__name=MEMBER_ROLE_MEMBER, user__isnull=False), then=Value(4))
        ]
        members_qs = personal_shared_team.team_members.annotate(
            order_field=Case(*order_whens, output_field=IntegerField(), default=Value(4))
        ).order_by("order_field").select_related('user').select_related('role')
        if exclude_owner:
            members_qs = members_qs.exclude(role_id=MEMBER_ROLE_OWNER)
        if is_added_by_group is not None:
            members_qs = members_qs.filter(is_added_by_group=is_added_by_group)
        return members_qs

    def get_shared_groups(self, personal_share_team):
        """
        Get list shared groups of the shared team
        :param personal_share_team:
        :return:
        """
        groups_qs = personal_share_team.groups.all().order_by('-id').select_related('enterprise_group')
        return groups_qs

    def delete_share_with_me(self, user: User):
        member_teams = user.team_members.filter(
            team__key__isnull=False, team__personal_share=True
        ).exclude(role__name=MEMBER_ROLE_OWNER)
        shared_teams = member_teams.values_list('team_id', flat=True)
        owners = TeamMember.objects.filter(
            team__key__isnull=False, role_id=MEMBER_ROLE_OWNER, team_id__in=shared_teams
        ).values_list('user_id', flat=True)
        member_teams.delete()
        return owners
