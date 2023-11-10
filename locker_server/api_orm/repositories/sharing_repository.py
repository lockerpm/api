import uuid
from typing import Union, Optional, List

from django.db.models import When, Q, IntegerField, Value, Case, Count, OuterRef, Subquery, CharField

from locker_server.api_orm.model_parsers.wrapper import get_model_parser
from locker_server.api_orm.models.wrapper import get_team_model, get_team_member_model, get_cipher_model, \
    get_collection_model, get_folder_model, get_member_role_model, get_user_model, get_group_model, \
    get_group_member_model, get_enterprise_group_model
from locker_server.api_orm.utils.revision_date import bump_account_revision_date
from locker_server.core.entities.cipher.cipher import Cipher
from locker_server.core.entities.cipher.folder import Folder
from locker_server.core.entities.enterprise.group.group import EnterpriseGroup
from locker_server.core.entities.member.member_role import MemberRole
from locker_server.core.entities.team.collection import Collection
from locker_server.core.entities.member.team_member import TeamMember
from locker_server.core.entities.team.group import Group
from locker_server.core.entities.team.team import Team
from locker_server.core.repositories.sharing_repository import SharingRepository
from locker_server.shared.constants.members import *
from locker_server.shared.utils.app import now
from locker_server.shared.utils.id_generator import timestamp_id_generator


UserORM = get_user_model()
TeamORM = get_team_model()
TeamMemberORM = get_team_member_model()
MemberRoleORM = get_member_role_model()
CipherORM = get_cipher_model()
FolderORM = get_folder_model()
CollectionORM = get_collection_model()
GroupORM = get_group_model()
GroupMemberORM = get_group_member_model()
EnterpriseGroupORM = get_enterprise_group_model()
ModelParser = get_model_parser()


class SharingORMRepository(SharingRepository):

    @staticmethod
    def _get_team_member_orm(team_member_id: int) -> Optional[TeamMemberORM]:
        try:
            team_member_orm = TeamMemberORM.objects.get(id=team_member_id)
            return team_member_orm
        except TeamMemberORM.DoesNotExist:
            return None

    @staticmethod
    def _get_cipher_orm(cipher_id: str) -> Optional[CipherORM]:
        try:
            return CipherORM.objects.get(id=cipher_id)
        except CipherORM.DoesNotExist:
            return None

    @staticmethod
    def _get_folder_orm(folder_id: str) -> Optional[FolderORM]:
        try:
            return FolderORM.objects.get(id=folder_id)
        except FolderORM.DoesNotExist:
            return None

    @staticmethod
    def _get_collection_orm(collection_id: str) -> Optional[CollectionORM]:
        try:
            return CollectionORM.objects.get(id=collection_id)
        except CollectionORM.DoesNotExist:
            return None

    @staticmethod
    def _get_team_orm(team_id: str) -> Optional[TeamORM]:
        try:
            return TeamORM.objects.get(id=team_id)
        except TeamORM.DoesNotExist:
            return None

    @staticmethod
    def _get_group_orm(group_id: str) -> Optional[GroupORM]:
        try:
            return GroupORM.objects.get(id=group_id)
        except GroupORM.DoesNotExist:
            return None

    @staticmethod
    def __create_shared_member_orm(team_orm: TeamORM, member_data, shared_collection_id=None):
        shared_member_orm, is_created = team_orm.team_members.model.retrieve_or_create_with_group(team_orm.id, **{
            "user_id": member_data.get("user_id"),
            "email": member_data.get("email"),
            "key": member_data.get("key"),
            "is_added_by_group": member_data.get("is_added_by_group", False),
            "status": member_data.get("status") or PM_MEMBER_STATUS_INVITED,
            "role_id": member_data.get("role"),
            "group": member_data.get("group")
        })
        # Update key:
        if is_created is False and member_data.get("key"):
            shared_member_orm.key = member_data.get("key")
            shared_member_orm.save()

        # Create collection for this shared member
        if shared_member_orm.role_id in [MEMBER_ROLE_MANAGER, MEMBER_ROLE_MEMBER] and shared_collection_id:
            shared_member_orm.collections_members.model.retrieve_or_create(
                collection_id=shared_collection_id, member_id=shared_member_orm.id,
                hide_passwords=member_data.get("hide_passwords", False)
            )
        # DEPRECATED: Not use hide_passwords
        # if shared_member.role_id in [MEMBER_ROLE_MEMBER]:
        #     shared_member.hide_passwords = member.get("hide_passwords", False)
        #     shared_member.save()
        return shared_member_orm

    @staticmethod
    def _share_cipher_orm(cipher_orm: CipherORM, team_id: str, cipher_data) -> CipherORM:
        # Update the cipher object
        cipher_orm.revision_date = now()
        cipher_orm.reprompt = cipher_data.get("reprompt", cipher_orm.reprompt) or 0
        cipher_orm.score = cipher_data.get("score", cipher_orm.score)
        cipher_orm.type = cipher_data.get("type", cipher_orm.type)
        cipher_orm.data = cipher_data.get("data", cipher_orm.get_data())
        cipher_orm.user_id = None
        cipher_orm.team_id = team_id
        cipher_orm.save()
        return cipher_orm

    @staticmethod
    def _stop_share_cipher_orm(cipher_orm: CipherORM, user_id: int, cipher_data):
        # Change team cipher to user cipher
        cipher_orm.revision_date = now()
        cipher_orm.reprompt = cipher_data.get("reprompt", cipher_orm.reprompt) or 0
        cipher_orm.score = cipher_data.get("score", cipher_orm.score)
        cipher_orm.type = cipher_data.get("type", cipher_orm.type)
        cipher_orm.data = cipher_data.get("data", cipher_orm.get_data())
        cipher_orm.user_id = user_id
        cipher_orm.team_id = None
        cipher_orm.save()
        return cipher_orm

    # ------------------------ List Sharing resource ------------------- #
    def list_sharing_invitations(self, user_id: int, personal_share: bool = True) -> List[TeamMember]:
        member_invitations_orm = TeamMemberORM.objects.filter(
            user_id=user_id, status__in=[PM_MEMBER_STATUS_INVITED, PM_MEMBER_STATUS_ACCEPTED],
            team__personal_share=personal_share,
        ).select_related('team').order_by('access_time')
        return [ModelParser.team_parser().parse_team_member(team_member_orm=m) for m in member_invitations_orm]

    def list_my_personal_share_teams(self, user_id: int, **filter_params) -> List[Team]:
        teams_orm = TeamORM.objects.filter(
            team_members__user_id=user_id,
            team_members__role_id=MEMBER_ROLE_OWNER,
            team_members__status=PM_MEMBER_STATUS_CONFIRMED,
            key__isnull=False,
            personal_share=True
        )
        type_param = filter_params.get("type")
        if type_param:
            teams_orm = teams_orm.annotate(collection_count=Count('collections'))
            if type_param == "item":
                teams_orm = teams_orm.exclude(collection_count__gte=1)
            elif type_param == "folder":
                teams_orm = teams_orm.filter(collection_count__gte=1)
        return [ModelParser.team_parser().parse_team(team_orm=team_orm) for team_orm in teams_orm]

    # ------------------------ Get Sharing resource --------------------- #
    def get_shared_members(self, personal_shared_team: Team,
                           exclude_owner=True, is_added_by_group=None) -> List[TeamMember]:
        order_whens = [
            When(Q(role__name=MEMBER_ROLE_OWNER, user__isnull=False), then=Value(2)),
            When(Q(role__name=MEMBER_ROLE_ADMIN, user__isnull=False), then=Value(3)),
            When(Q(role__name=MEMBER_ROLE_MEMBER, user__isnull=False), then=Value(4))
        ]
        members_orm = TeamMemberORM.objects.filter(team_id=personal_shared_team.team_id).annotate(
            order_field=Case(*order_whens, output_field=IntegerField(), default=Value(4))
        ).order_by("order_field").select_related('user').select_related('role').select_related('team')
        if exclude_owner:
            members_orm = members_orm.exclude(role_id=MEMBER_ROLE_OWNER)
        if is_added_by_group is not None:
            members_orm = members_orm.filter(is_added_by_group=is_added_by_group)

        return [ModelParser.team_parser().parse_team_member(team_member_orm=member_orm) for member_orm in members_orm]

    def get_share_cipher(self, sharing_id: str) -> Optional[Cipher]:
        share_cipher_orm = CipherORM.objects.filter(team_id=sharing_id).first()
        return ModelParser.cipher_parser().parse_cipher(cipher_orm=share_cipher_orm) if share_cipher_orm else None

    def get_sharing_cipher_type(self, sharing_id: str) -> Union[str, int]:
        share_cipher_orm = CipherORM.objects.filter(team_id=sharing_id).first()
        return share_cipher_orm.type if share_cipher_orm else None

    def get_share_collection(self, sharing_id: str) -> Optional[Collection]:
        collection_orm = CollectionORM.objects.filter(team_id=sharing_id).first()
        return ModelParser.team_parser().parse_collection(collection_orm=collection_orm) if collection_orm else None

    # ------------------------ Create Sharing resource --------------------- #
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
        folder_orm = self._get_folder_orm(folder_id=folder.folder_id) if folder else None
        cipher_orm = self._get_cipher_orm(cipher_id=cipher.cipher_id) if cipher else None

        if folder_orm:
            user_orm = folder_orm.user
        else:
            if cipher_orm.team:
                user_orm = cipher_orm.team.team_members.get(role_id=MEMBER_ROLE_OWNER, is_primary=True).user
            else:
                user_orm = cipher_orm.user

        # If the cipher is shared => The sharing team is the team of the cipher
        if cipher_orm and cipher_orm.team:
            new_sharing_orm = cipher_orm.team
        # Else, create new sharing team
        else:
            # from cystack_models.models.members.member_roles import MemberRole
            # Create new sharing id
            id_generator = timestamp_id_generator(user_id=user_orm.user_id)
            sharing_id = next(id_generator)
            try:
                team_name = user_orm.full_name
            except AttributeError:
                team_name = user_orm.get_from_cystack_id().get("full_name", "Sharing")

            new_sharing_orm = TeamORM.create(**{
                "id": sharing_id,
                "name": team_name,
                "description": "",
                "personal_share": True,
                "members": [{
                    "user_id": user_orm.user_id,
                    "role": MemberRoleORM.objects.get(name=MEMBER_ROLE_OWNER),
                    "is_default": False,
                    "is_primary": True
                }]
            })
            new_sharing_orm.key = sharing_key
            new_sharing_orm.revision_date = now()
            new_sharing_orm.save()

            # Save owner key for primary member
            primary_member_orm = new_sharing_orm.team_members.get(user=user_orm)
            primary_member_orm.key = sharing_key
            primary_member_orm.external_id = uuid.uuid4()
            primary_member_orm.save()

        # If user shares a folder => Create collection for this team
        shared_collection_orm = None
        if shared_collection_name:
            shared_collection_orm = new_sharing_orm.collections.model.create(new_sharing_orm, **{
                "name": shared_collection_name, "is_default": False
            })

        # Create sharing members
        existed_member_users, non_existed_member_users = self.add_members(
            team_id=new_sharing_orm.id,
            shared_collection_id=shared_collection_orm.id if shared_collection_orm else None,
            members=members,
            groups=groups
        )

        # Sharing the folder
        if folder_orm and shared_collection_orm:
            shared_collection_cipher_ids = [collection_cipher["id"] for collection_cipher in shared_collection_ciphers]
            ciphers_orm = user_orm.ciphers.filter(id__in=shared_collection_cipher_ids)
            shared_cipher_ids = []
            # Update new cipher data
            for cipher_orm in ciphers_orm:
                shared_cipher_data = next(
                    (item for item in shared_collection_ciphers if item["id"] == cipher_orm.id), {}
                )
                shared_cipher_ids.append(cipher_orm.id)
                self._share_cipher_orm(cipher_orm=cipher_orm, team_id=new_sharing_orm.id, cipher_data=shared_cipher_data)

            # Delete all folders of the ciphers
            CipherORM.objects.filter(id__in=shared_cipher_ids).update(folders="")
            # Create a collection for the shared ciphers
            shared_collection_orm.collections_ciphers.model.create_multiple_for_collection(
                shared_collection_orm.id, *shared_cipher_ids
            )
            # Then, delete the root folder
            folder_orm.delete()

        # Share a single cipher
        if cipher_orm:
            if not cipher_orm.team:
                self._share_cipher_orm(cipher_orm=cipher_orm, team_id=new_sharing_orm.id, cipher_data=shared_cipher_data)

        # Update revision date of the user
        bump_account_revision_date(team=new_sharing_orm)

        new_sharing = ModelParser.team_parser().parse_team(team_orm=new_sharing_orm)
        return new_sharing, existed_member_users, non_existed_member_users

    # ------------------------ Update Sharing resource --------------------- #
    def accept_invitation(self, member: TeamMember) -> Optional[TeamMember]:
        member_orm = self._get_team_member_orm(team_member_id=member.team_member_id)
        if not member_orm:
            return None
        if member_orm.key:
            member_orm.status = PM_MEMBER_STATUS_CONFIRMED

        # Else, set status ACCEPTED
        else:
            member_orm.status = PM_MEMBER_STATUS_ACCEPTED
        member_orm.save()
        bump_account_revision_date(user=member_orm.user)
        member.status = member_orm.status
        return member

    def reject_invitation(self, member: TeamMember):
        try:
            return TeamMemberORM.objects.get(id=member.team_member_id).delete()
        except TeamMemberORM.DoesNotExist:
            return None

    def confirm_invitation(self, member: TeamMember, key: str):
        member_orm = self._get_team_member_orm(team_member_id=member.team_member_id)
        if not member_orm:
            return None
        member_orm.email = None
        member_orm.key = key
        member_orm.status = PM_MEMBER_STATUS_CONFIRMED
        member_orm.save()
        bump_account_revision_date(user=member_orm.user)

        member.status = member_orm.status
        member.key = member_orm.key
        member.email = None
        return member

    def update_role_invitation(self, member: TeamMember, role_id: str,
                               hide_passwords: bool = None) -> Optional[TeamMember]:
        member_orm = self._get_team_member_orm(team_member_id=member.team_member_id)
        if not member_orm:
            return None
        member_orm.role_id = role_id
        if role_id in [MEMBER_ROLE_MEMBER]:
            member_orm.hide_passwords = hide_passwords
        member_orm.save()
        # Bump revision date
        bump_account_revision_date(user=member_orm.user)

        member.role = MemberRole(name=role_id)
        member.hide_passwords = member_orm.hide_passwords
        return member

    def add_members(self, team_id: str, shared_collection_id: str, members: List, groups: List = None):
        primary_member = TeamMemberORM.objects.get(is_primary=True, team_id=team_id)
        primary_user = primary_member.user
        non_existed_member_users = []
        existed_member_users = []
        existed_user_ids = list(TeamMemberORM.objects.filter(
            user_id__isnull=False, team_id=team_id
        ).values_list('user_id', flat=True))
        existed_emails = list(TeamMemberORM.objects.filter(
            email__isnull=False, team_id=team_id
        ).values_list('email', flat=True))
        for member in members:
            if member.get("user_id") == primary_user.user_id:
                continue
            # Retrieve activated user
            try:
                member_user_id = UserORM.objects.get(user_id=member.get("user_id"), activated=True).user_id
                email = None
            except UserORM.DoesNotExist:
                member_user_id = None
                email = member.get("email")
            # if member_user and member_user.user_id in existed_user_ids:
            #     team.team_members.filter(user_id=member_user.user_id).update(is_added_by_group=False)
            #     continue
            # if email and email in existed_emails:
            #     team.team_members.filter(email=email).update(is_added_by_group=False)
            #     continue
            member_data = {"user_id": member_user_id, "email": email, "role": member.get("role"), "key": member.get("key")}
            shared_member_orm = self.__create_shared_member_orm(
                team_orm=primary_member.team, member_data=member_data, shared_collection_id=shared_collection_id
            )
            # Make sure the shared member is added as single person and role is set by member_data
            shared_member_orm.is_added_by_group = False
            shared_member_orm.role_id = member.get("role")
            shared_member_orm.save()
            # Append to existed_member_users and non_existed_member_users list
            if shared_member_orm.user_id and shared_member_orm.user_id not in existed_user_ids:
                existed_member_users.append(shared_member_orm.user_id)
                existed_user_ids.append(shared_member_orm.user_id)
            if shared_member_orm.email and shared_member_orm.email not in existed_emails:
                non_existed_member_users.append(shared_member_orm.email)
                existed_emails.append(shared_member_orm.email)

        if groups:
            existed_group_member_users, non_existed_group_member_users = self.add_group_members(
                team_id=team_id, shared_collection_id=shared_collection_id, groups=groups
            )
            existed_member_users += existed_group_member_users
            non_existed_member_users += non_existed_group_member_users
        return list(set(existed_member_users)), list(set(non_existed_member_users))

    def add_group_members(self, team_id: str, shared_collection_id: str, groups):
        primary_member = TeamMemberORM.objects.get(is_primary=True, team_id=team_id)
        primary_user = primary_member.user
        team_orm = primary_member.team
        non_existed_member_users = []
        existed_member_users = []
        existed_user_ids = list(team_orm.team_members.filter(user_id__isnull=False).values_list('user_id', flat=True))
        existed_emails = list(team_orm.team_members.filter(email__isnull=False).values_list('email', flat=True))

        members_groups_data = [group.get("members") or [] for group in groups]
        members_groups_user_ids = []
        for members_group_data in members_groups_data:
            members_groups_user_ids += [m.get("user_id") for m in members_group_data if m.get("user_id")]
        members_groups_users_orm = UserORM.objects.filter(user_id__in=members_groups_user_ids, activated=True)
        members_groups_users_dict = dict()
        for u in members_groups_users_orm:
            members_groups_users_dict[u.user_id] = u

        for group in groups:
            members = group.get("members") or []
            team_group_orm = team_orm.groups.model.retrieve_or_create(
                team_orm.id, group.get("id"), **{
                    "role_id": group.get("role") or group.get("role_id") or MEMBER_ROLE_MEMBER
                }
            )
            for member in members:
                if member.get("user_id") == primary_user.user_id:
                    continue
                member_user_orm = members_groups_users_dict.get(member.get("user_id"))
                email = None if member_user_orm else member.get("email")

                # if member_user and member_user.user_id in existed_user_ids:
                #     # TODO: Check the member is in group or not. If the member group doesnt exist, create member group
                #     continue
                # if email and email in existed_emails:
                #     # TODO: Check the member is in group or not. If the member group doesnt exist, create member group
                #     continue
                member_data = {
                    "user_id": member_user_orm.user_id,
                    "email": email,
                    "role": member.get("role"),
                    "key": member.get("key"),
                    "status": PM_MEMBER_STATUS_CONFIRMED if member.get("key") else PM_MEMBER_STATUS_INVITED,
                    "is_added_by_group": True,
                    "group": team_group_orm,
                }
                shared_member = self.__create_shared_member_orm(
                    team_orm=team_orm, member_data=member_data, shared_collection_id=shared_collection_id
                )
                if shared_member.user_id and shared_member.user_id not in existed_user_ids:
                    existed_member_users.append(shared_member.user_id)
                    existed_user_ids.append(shared_member.user_id)
                if shared_member.email and shared_member.email not in existed_emails:
                    non_existed_member_users.append(shared_member.email)
                    existed_emails.append(shared_member.email)
        return existed_member_users, non_existed_member_users

    def stop_sharing(self, member: TeamMember = None, group: Group = None,
                     cipher: Cipher = None, cipher_data=None,
                     collection: Collection = None, personal_folder_name: str = None, personal_folder_ciphers=None):
        team = group.team if group else member.team
        sharing_id = team.team_id
        team_orm = self._get_team_orm(team_id=sharing_id)

        # Get owner
        user_owner_orm = TeamMemberORM.objects.get(is_primary=True, team_id=sharing_id, role_id=MEMBER_ROLE_OWNER).user

        # Remove this member / group from the team
        deleted_members_user_ids = []
        group_orm = None
        if group:
            group_orm = self._get_group_orm(group_id=group.group_id)
            # Check members are shared by User 1-1 (not by Group)
            group_members_user_ids = list(group_orm.groups_members.values_list('member__user_id', flat=True))
            team_members_orm = team_orm.team_members.filter(
                user_id__in=group_members_user_ids, is_added_by_group=True
            ).annotate(
                group_count=Count('groups_members')
            )

            # Filter list members have only one group. Then delete them
            deleted_members = team_members_orm.filter(group_count=1)
            deleted_members_user_ids = list(deleted_members.values_list('user_id', flat=True))
            deleted_members.delete()
            # Filter list members have other groups => Set role_id by other groups
            first_group_subquery = GroupMemberORM.objects.exclude(group_id=group_orm.id).filter(
                member_id=OuterRef('id')
            ).order_by('group_id')
            more_one_groups_orm = team_members_orm.filter(group_count__gt=1).annotate(
                first_group_role=Subquery(first_group_subquery.values('group__role_id')[:1], output_field=CharField())
            )
            for m in more_one_groups_orm:
                if m.first_group_role:
                    m.role_id = m.first_group_role
                    m.save()
            # Delete this group
            group_orm.delete()
        member_orm = None
        if member:
            member_orm = self._get_team_member_orm(team_member_id=member.team_member_id)
            group_member_orm = member_orm.groups_members.all().order_by('group__creation_date').first()
            if not group_member_orm:
                deleted_members_user_ids = [member_orm.user_id]
                member_orm.delete()
            else:
                member_orm.is_added_by_group = True
                member_orm.role_id = group_member_orm.group.role_id
                member_orm.save()

        # If the team does not have any members (excluding owner)
        # => Remove shared team and change the cipher/collection to personal cipher/personal folder
        if team_orm.team_members.exclude(role_id=MEMBER_ROLE_OWNER).exists() is False:
            self.stop_share_all_members(team_id=team_orm.id, cipher=cipher, cipher_data=cipher_data,
                                        collection=collection, personal_folder_name=personal_folder_name,
                                        personal_folder_ciphers=personal_folder_ciphers)

        # Update revision date of user
        if group:
            bump_account_revision_date(team=team_orm, **{"group_ids": [group_orm.enterprise_group_id]})
        else:
            bump_account_revision_date(user=member_orm.user)
        bump_account_revision_date(user=user_owner_orm)

        return deleted_members_user_ids

    def stop_share_all_members(self, team_id: str, cipher: Cipher = None, cipher_data=None,
                               collection: Collection = None, personal_folder_name: str = None,
                               personal_folder_ciphers=None):
        # Get owner
        user_owner_orm = TeamMemberORM.objects.get(is_primary=True, team_id=team_id, role_id=MEMBER_ROLE_OWNER).user
        other_members = list(
            TeamMemberORM.objects.filter(team_id=team_id).exclude(user=user_owner_orm).values_list('user_id', flat=True)
        )

        # If the team shared a folder
        personal_folder_id = None
        if collection:
            # Create personal folder of the owner
            personal_folder_orm = FolderORM(
                name=personal_folder_name, user=user_owner_orm, creation_date=now(), revision_date=now()
            )
            personal_folder_orm.save()
            personal_folder_id = personal_folder_orm.id
            # Get all ciphers of the shared team
            shared_folder_cipher_ids = [c["id"] for c in personal_folder_ciphers]
            ciphers_orm = CipherORM.objects.filter(team_id=team_id, id__in=shared_folder_cipher_ids)

            # Update new cipher data
            for c in ciphers_orm:
                personal_cipher_data = next(
                    (item for item in personal_folder_ciphers if item["id"] == c.id), {}
                )
                self._stop_share_cipher_orm(
                    cipher_orm=c, user_id=user_owner_orm.user_id, cipher_data=personal_cipher_data
                )

            # Update folder
            CipherORM.objects.filter(id__in=shared_folder_cipher_ids).update(
                folders=str({user_owner_orm.user_id: str(personal_folder_orm.id)})
            )

        # If the team shared a cipher
        if cipher:
            cipher_orm = self._get_cipher_orm(cipher_id=cipher.cipher_id)
            self._stop_share_cipher_orm(cipher_orm=cipher_orm, user_id=user_owner_orm.user_id, cipher_data=cipher_data)

        # Delete this team
        team_orm = self._get_team_orm(team_id=team_id)
        team_orm.ciphers.all().delete()
        team_orm.collections.all().delete()
        team_orm.groups.all().delete()
        team_orm.delete()

        # Update revision date of user
        bump_account_revision_date(user=user_owner_orm)
        return other_members, personal_folder_id

    def leave_sharing(self, member: TeamMember) -> int:
        member_orm = self._get_team_member_orm(team_member_id=member.team_member_id)
        bump_account_revision_date(user=member_orm.user)
        member_user_id = member_orm.user_id
        member_orm.delete()
        return member_user_id

    def update_share_folder(self, collection: Collection, name: str, groups=None, revision_date=None) -> Collection:
        collection_orm = self._get_collection_orm(collection_id=collection.collection_id)
        collection_orm.name = name
        collection_orm.revision_date = revision_date or now()
        collection_orm.save()
        # if groups:
        #     collection.collections_groups.all().delete()
        #     groups_data = [{"id": group_id} for group_id in groups]
        #     collection.collections_groups.model.create_multiple(collection, *groups_data)
        bump_account_revision_date(team=collection_orm.team)
        collection.name = name
        collection.revision_date = now()
        return collection

    def delete_share_folder(self, collection: Collection,
                            personal_folder_name: str = None, personal_folder_ciphers=None):
        # Get owner
        team_orm = self._get_team_orm(team_id=collection.team.team_id)
        user_owner_orm = team_orm.team_members.get(role_id=MEMBER_ROLE_OWNER, is_primary=True).user
        other_members = list(team_orm.team_members.exclude(user=user_owner_orm).values_list('user_id', flat=True))

        # Get all ciphers of the shared team
        shared_folder_cipher_ids = [cipher["id"] for cipher in personal_folder_ciphers]
        ciphers_orm = team_orm.ciphers.filter(id__in=shared_folder_cipher_ids)

        # Update new cipher data
        for c in ciphers_orm:
            personal_cipher_data = next(
                (item for item in personal_folder_ciphers if item["id"] == c.id), {}
            )
            self._stop_share_cipher_orm(cipher_orm=c, user_id=user_owner_orm.user_id, cipher_data=personal_cipher_data)

        # Move ciphers to the trash
        CipherORM.objects.filter(id__in=shared_folder_cipher_ids).update(revision_date=now(), deleted_date=now())

        # Delete this team
        team_orm.ciphers.all().delete()
        team_orm.collections.all().delete()
        team_orm.groups.all().delete()
        team_orm.delete()

        # Update revision date of user
        bump_account_revision_date(user=user_owner_orm)
        return other_members

    def add_group_member_to_share(self, enterprise_group: EnterpriseGroup, new_member_ids: List[str]):
        enterprise_group_orm = EnterpriseGroupORM.objects.get(id=enterprise_group.enterprise_group_id)
        enterprise_group_member_user_ids = enterprise_group_orm.group_members.filter(
            member_id__in=new_member_ids
        ).values_list('member__user_id', flat=True)
        sharing_groups = enterprise_group_orm.sharing_groups.select_related('team').prefetch_related('groups_members')
        members = [{"user_id": user_id, "key": None} for user_id in enterprise_group_member_user_ids]

        confirmed_data = []
        for sharing_group in sharing_groups:
            team = sharing_group.team
            try:
                owner_user = TeamMemberORM.objects.get(is_primary=True, team_id=team.id).user
            except TeamMemberORM.DoesNotExist:
                continue
            collection = team.collections.first()
            groups = [{
                "id": sharing_group.enterprise_group_id,
                "role": sharing_group.role_id,
                "members": members
            }]
            existed_member_users, non_existed_member_users = self.add_group_members(
                team_id=team.id, shared_collection_id=collection.id if collection else None, groups=groups
            )
            if collection:
                shared_type_name = "folder"
            else:
                cipher_obj = team.ciphers.first()
                shared_type_name = cipher_obj.type if cipher_obj else None
            confirmed_data.append({
                "id": team.id,
                "name": team.name,
                "owner": owner_user.user_id,
                "group_id": sharing_group.enterprise_group_id,
                "group_name": sharing_group.name,
                "shared_type_name": shared_type_name,
                "existed_member_users": existed_member_users,
                "non_existed_member_users": non_existed_member_users,
            })
        return confirmed_data

    # ------------------------ Delete Sharing resource --------------------- #

