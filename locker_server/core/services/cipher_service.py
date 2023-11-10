from typing import List, Optional, Dict

from locker_server.core.entities.cipher.cipher import Cipher
from locker_server.core.entities.member.team_member import TeamMember
from locker_server.core.entities.user.user import User
from locker_server.core.exceptions.cipher_exception import FolderDoesNotExistException, CipherMaximumReachedException, \
    CipherDoesNotExistException
from locker_server.core.exceptions.collection_exception import CollectionDoesNotExistException, \
    CollectionCannotRemoveException, CollectionCannotAddException
from locker_server.core.exceptions.team_exception import TeamDoesNotExistException, TeamLockedException
from locker_server.core.exceptions.team_member_exception import OnlyAllowOwnerUpdateException
from locker_server.core.repositories.cipher_repository import CipherRepository
from locker_server.core.repositories.folder_repository import FolderRepository
from locker_server.core.repositories.team_member_repository import TeamMemberRepository
from locker_server.core.repositories.team_repository import TeamRepository
from locker_server.core.repositories.user_plan_repository import UserPlanRepository
from locker_server.shared.constants.members import *
from locker_server.shared.utils.app import diff_list


class CipherService:
    """
    This class represents Use Cases related Cipher
    """

    def __init__(self, cipher_repository: CipherRepository,
                 folder_repository: FolderRepository,
                 team_repository: TeamRepository,
                 team_member_repository: TeamMemberRepository,
                 user_plan_repository: UserPlanRepository):
        self.cipher_repository = cipher_repository
        self.folder_repository = folder_repository
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.user_plan_repository = user_plan_repository

    def _validate_folder(self, user_id: int, folder_id: str) -> str:
        if folder_id:
            if not self.cipher_repository.get_user_folder(folder_id=folder_id, user_id=user_id):
                raise FolderDoesNotExistException
        return folder_id

    def _validated_team(self, user: User, data, view_action: str, specific_validate_collections_func: str = None):
        organization_id = data.get("organization_id") or data.get("organizationId")
        collection_ids = data.get("collection_ids", []) or data.get("collectionIds", [])
        # Check the permission in the organization_id
        allow_roles = [MEMBER_ROLE_OWNER]
        if view_action == "update":
            allow_roles.append(MEMBER_ROLE_ADMIN)
        if organization_id:
            team_member = self.team_member_repository.get_user_team_member(
                user_id=user.user_id, team_id=organization_id
            )
            if not team_member:
                raise TeamDoesNotExistException
            if team_member.role.name not in allow_roles:
                group_member_roles = self.team_member_repository.list_group_member_roles(team_member=team_member)
                is_allowed = any(role_id in allow_roles for role_id in group_member_roles)
                if not is_allowed:
                    raise TeamDoesNotExistException
            # Get team object and check team is locked?
            team_obj = team_member.team
            if not team_obj.key:
                raise TeamDoesNotExistException
            if team_obj.locked:
                raise TeamLockedException
            data["team"] = team_obj
            if specific_validate_collections_func == "validate_update_collections":
                data["collectionIds"] = self._validate_update_collections(
                    team_member=team_member, collection_ids=collection_ids
                )
            else:
                data["collectionIds"] = self._validate_collections(
                    team_member=team_member, collection_ids=collection_ids
                )
        else:
            data["organizationId"] = None
            data["collectionIds"] = []
            data["team"] = None
        return data

    def _validate_collections(self, team_member: TeamMember, collection_ids: List[str]):
        team_obj = team_member.team
        role_id = team_member.role.name
        if not collection_ids:
            default_collection = self.team_repository.get_default_collection(team_id=team_obj.team_id)
            if not default_collection:
                raise TeamDoesNotExistException
            return [default_collection.collection_id]
        else:
            if role_id in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]:
                team_collections_ids = self.team_repository.list_team_collection_ids(team_id=team_obj.team_id)
            else:
                team_collections_ids = self.team_member_repository.list_member_collection_ids(
                    team_member_id=team_member.team_member_id
                )
            for collection_id in collection_ids:
                if collection_id not in list(team_collections_ids):
                    raise CollectionDoesNotExistException(collection_id=collection_id)

            return list(set(collection_ids))

    def _validate_update_collections(self, team_member: TeamMember, collection_ids: List[str]):
        team_obj = team_member.team
        if not collection_ids:
            default_collection = self.team_repository.get_default_collection(team_id=team_obj.team_id)
            if not default_collection:
                return []
            return [default_collection.collection_id]
        else:
            team_collections_ids = self.team_repository.list_team_collection_ids(team_id=team_obj.team_id)
            for collection_id in collection_ids:
                if collection_id not in list(team_collections_ids):
                    raise CollectionDoesNotExistException(collection_id=collection_id)
            return list(set(collection_ids))

    def _validated_plan(self, user: User, data):
        cipher_type = data.get("type")
        # Get limit cipher type from personal and team plans
        allow_cipher_type = self.user_plan_repository.get_max_allow_cipher_type(user=user)
        existed_ciphers_count = self.cipher_repository.count_ciphers_created_by_user(
            user_id=user.user_id, **{"type": cipher_type}
        )
        if allow_cipher_type.get(cipher_type) and existed_ciphers_count >= allow_cipher_type.get(cipher_type):
            raise CipherMaximumReachedException
        return data

    def get_master_pwd_item(self, user_id: int) -> Optional[Cipher]:
        return self.cipher_repository.get_master_pwd_item(user_id=user_id)

    def create_cipher(self, user: User, cipher_data: Dict, view_action: str = None, check_plan: bool = True) -> Cipher:
        # Check folder id
        self._validate_folder(user_id=user.user_id, folder_id=cipher_data.get("folderId"))
        # Check team and collection ids
        cipher_data = self._validated_team(
            user=user, data=cipher_data, view_action=view_action
        )
        # Check the current plan of the user
        if check_plan:
            cipher_data = self._validated_plan(user=user, data=cipher_data)
        # Create new cipher object
        new_cipher = self.cipher_repository.create_cipher(cipher_data=cipher_data)
        return new_cipher

    def update_cipher(self, cipher: Cipher, user: User, cipher_data: Dict, view_action: str = None) -> Cipher:
        user_id = user.user_id
        # Check the folder id
        self._validate_folder(user_id=user_id, folder_id=cipher_data.get("folderId"))

        # Validate team and collection ids
        cipher_data = self._validated_team(
            user=user, data=cipher_data, view_action=view_action,
            specific_validate_collections_func="validate_update_collections"
        )
        team = cipher_data.get("team")

        if not team and cipher.team:
            team_member = self.team_member_repository.get_user_team_member(user_id=user_id, team_id=cipher.team.team_id)
            if not team_member or team_member.role.name != MEMBER_ROLE_OWNER:
                raise OnlyAllowOwnerUpdateException

        # Validate collection ids
        if team and team.team_id == cipher.team.team_id:
            team_member = self.team_member_repository.get_user_team_member(user_id=user_id, team_id=cipher.team.team_id)
            if not team_member:
                raise TeamDoesNotExistException

            group_member_roles = self.team_member_repository.list_group_member_roles(team_member=team_member)
            real_role = min([MAP_MEMBER_TYPE_BW.get(r) for r in group_member_roles + [team_member.role.name]])
            role_id = MAP_MEMBER_TYPE_FROM_BW.get(real_role)
            if role_id not in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]:
                raise TeamDoesNotExistException

            cipher_collection_ids = self.cipher_repository.list_cipher_collection_ids(cipher_id=cipher.cipher_id)
            collection_ids = cipher_data.get("collectionIds", [])
            if role_id in [MEMBER_ROLE_OWNER, MEMBER_ROLE_ADMIN]:
                member_collection_ids = self.team_repository.list_team_collection_ids(team_id=team.team_id)
            else:
                member_collection_ids = self.team_member_repository.list_member_collection_ids(
                    team_member_id=team_member.team_member_id
                )
            remove_collection_ids = diff_list(cipher_collection_ids, collection_ids)
            add_collection_ids = diff_list(collection_ids, cipher_collection_ids)
            if remove_collection_ids:
                for member_collection_id in member_collection_ids:
                    if member_collection_id not in remove_collection_ids:
                        raise CollectionCannotRemoveException(collection_id=member_collection_id)
            if add_collection_ids:
                for member_collection_id in member_collection_ids:
                    if member_collection_id not in add_collection_ids:
                        raise CollectionCannotAddException(collection_id=member_collection_id)

        cipher = self.cipher_repository.update_cipher(cipher_id=cipher.cipher_id, cipher_data=cipher_data)
        return cipher

    def update_cipher_use(self, cipher: Cipher, cipher_use_data: Dict) -> Cipher:
        cipher = self.cipher_repository.update_cipher_use(cipher_id=cipher.cipher_id, cipher_use_data=cipher_use_data)
        if not cipher:
            raise CipherDoesNotExistException
        return cipher

    def move_multiple_cipher(self, cipher_ids: List[str], user_id_moved: int, folder_id: str):
        if folder_id:
            folder = self.folder_repository.get_by_id(folder_id=folder_id)
            if not folder or folder.user.user_id != user_id_moved:
                raise FolderDoesNotExistException
        moved_cipher_ids = self.cipher_repository.move_multiple_cipher(
            cipher_ids=cipher_ids, user_id_moved=user_id_moved, folder_id=folder_id
        )
        return moved_cipher_ids

    def check_member_belongs_cipher_collections(self, cipher: Cipher, member: TeamMember) -> bool:
        return self.cipher_repository.check_member_belongs_cipher_collections(cipher, member)

    def get_by_id(self, cipher_id: str) -> Optional[Cipher]:
        cipher = self.cipher_repository.get_by_id(cipher_id=cipher_id)
        if not cipher:
            raise CipherDoesNotExistException
        return cipher

    def get_multiple_by_ids(self, cipher_ids: List[str]) -> List[Cipher]:
        return self.cipher_repository.get_multiple_by_ids(cipher_ids=cipher_ids)

    def get_multiple_by_user(self, user_id: int, only_personal=False, only_managed_team=False,
                             only_edited=False, only_deleted=False,
                             exclude_team_ids=None, filter_ids=None, exclude_types=None) -> List[Cipher]:
        return self.cipher_repository.get_multiple_by_user(
            user_id=user_id, only_personal=only_personal, only_managed_team=only_managed_team,
            only_edited=only_edited, only_deleted=only_deleted, exclude_team_ids=exclude_team_ids,
            filter_ids=filter_ids, exclude_types=exclude_types
        )

    def sync_and_statistic_ciphers(self, user_id: int, only_personal=False, only_managed_team=False,
                                   only_edited=False, only_deleted=False,
                                   exclude_team_ids=None, filter_ids=None, exclude_types=None) -> Dict:
        return self.cipher_repository.sync_and_statistic_ciphers(
            user_id=user_id, only_personal=only_personal, only_managed_team=only_managed_team,
            only_edited=only_edited, only_deleted=only_deleted,
            exclude_team_ids=exclude_team_ids, filter_ids=filter_ids, exclude_types=exclude_types
        )

    def delete_multiple_ciphers(self, cipher_ids: List[str], user_id_deleted: int) -> List[str]:
        return self.cipher_repository.delete_multiple_cipher(
            cipher_ids=cipher_ids, user_id_deleted=user_id_deleted
        )

    def delete_permanent_multiple_cipher(self, cipher_ids: List[str], user_id_deleted) -> List[str]:
        return self.cipher_repository.delete_permanent_multiple_cipher(
            cipher_ids=cipher_ids, user_id_deleted=user_id_deleted
        )

    def restore_multiple_ciphers(self, cipher_ids: List[str], user_id_restored: int) -> List[str]:
        return self.cipher_repository.restore_multiple_cipher(
            cipher_ids=cipher_ids, user_id_restored=user_id_restored
        )

    def sync_personal_cipher_offline(self, user: User, ciphers, folders, folder_relationships):
        return self.cipher_repository.sync_personal_cipher_offline(
            user_id=user.user_id, ciphers=ciphers, folders=folders, folder_relationships=folder_relationships
        )

    def import_multiple_ciphers(self, user: User, ciphers: List):
        allow_cipher_type = self.user_plan_repository.get_max_allow_cipher_type(user=user)
        self.cipher_repository.import_multiple_ciphers(user=user, ciphers=ciphers, allow_cipher_type=allow_cipher_type)